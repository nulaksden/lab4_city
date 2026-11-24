import re
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from sqlmodel import Field, Session, SQLModel, create_engine, select

DSN = "postgresql+psycopg://postgres:postgres@localhost:5433/postgres"
engine = create_engine(DSN)


class City(SQLModel, table=True):
    __tablename__ = "cities"
    id: int | None = Field(default=None, primary_key=True)
    name: str
    zip_code: str


class District(SQLModel, table=True):
    __tablename__ = "districts"
    id: int | None = Field(default=None, primary_key=True)
    name: str
    city_id: int = Field(foreign_key="cities.id")


# Принцип Open/Closed (п. 10): абстрактний інтерфейс сховища
class BaseCityStorage(ABC):
    @abstractmethod
    def list_all(self) -> list[City]: ...

    @abstractmethod
    def get(self, city_id: int) -> City | None: ...

    @abstractmethod
    def add(self, city: City) -> City: ...

    @abstractmethod
    def update(self, city_id: int, data: City) -> City | None: ...

    @abstractmethod
    def delete(self, city_id: int) -> bool: ...


class PostgresCityStorage(BaseCityStorage):
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_all(self) -> list[City]:
        return list(self.session.exec(select(City)).all())

    def get(self, city_id: int) -> City | None:
        return self.session.get(City, city_id)

    def add(self, city: City) -> City:
        self.session.add(city)
        self.session.commit()
        self.session.refresh(city)
        return city

    def update(self, city_id: int, data: City) -> City | None:
        city = self.session.get(City, city_id)
        if not city:
            return None
        city.name, city.zip_code = data.name, data.zip_code
        self.session.add(city)
        self.session.commit()
        self.session.refresh(city)
        return city

    def delete(self, city_id: int) -> bool:
        city = self.session.get(City, city_id)
        if not city:
            return False
        self.session.delete(city)
        self.session.commit()
        return True


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    SQLModel.metadata.create_all(engine)
    yield


app = FastAPI(lifespan=lifespan)


def get_storage() -> Generator[BaseCityStorage, None, None]:
    with Session(engine) as session:
        yield PostgresCityStorage(session)


def validate_zip(zip_code: str) -> None:
    if not re.fullmatch(r"\d{5}", zip_code):
        raise HTTPException(status_code=400, detail="Індекс має містити рівно 5 цифр")


@app.get("/cities/")
def get_cities(storage: BaseCityStorage = Depends(get_storage)) -> list[City]:
    return storage.list_all()


@app.get("/cities/{city_id}")
def get_city(city_id: int, storage: BaseCityStorage = Depends(get_storage)) -> City:
    city = storage.get(city_id)
    if not city:
        raise HTTPException(status_code=404, detail="Місто не знайдено")
    return city


@app.post("/cities/", status_code=201)
def create_city(city: City, storage: BaseCityStorage = Depends(get_storage)) -> City:
    validate_zip(city.zip_code)
    return storage.add(city)


@app.put("/cities/{city_id}")
def update_city(
    city_id: int, data: City, storage: BaseCityStorage = Depends(get_storage)
) -> City:
    validate_zip(data.zip_code)
    city = storage.update(city_id, data)
    if not city:
        raise HTTPException(status_code=404, detail="Місто не знайдено")
    return city


@app.delete("/cities/{city_id}")
def delete_city(
    city_id: int, storage: BaseCityStorage = Depends(get_storage)
) -> dict[str, bool]:
    if not storage.delete(city_id):
        raise HTTPException(status_code=404, detail="Місто не знайдено")
    return {"ok": True}


@app.get("/districts/")
def get_districts() -> list[District]:
    with Session(engine) as session:
        return list(session.exec(select(District)).all())
