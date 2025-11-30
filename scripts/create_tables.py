from common.db import Base, engine
from services.users_service.models import User
from services.rooms_service.models import Room
from services.bookings_service.models import Booking
from services.reviews_service.models import Review

Base.metadata.create_all(bind=engine)
