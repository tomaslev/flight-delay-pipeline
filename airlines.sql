-- Airlines PostgreSQL schema for Flight Delay Prediction

DROP TABLE IF EXISTS FlightDelay;
DROP TABLE IF EXISTS DelayCause;
DROP TABLE IF EXISTS FlightAircraft;
DROP TABLE IF EXISTS FlightAirlines;
DROP TABLE IF EXISTS AirportOrigin;
DROP TABLE IF EXISTS AirportDestination;
DROP TABLE IF EXISTS Weather;
DROP TABLE IF EXISTS Flight;
DROP TABLE IF EXISTS Aircraft;
DROP TABLE IF EXISTS Airline;
DROP TABLE IF EXISTS Airport;

-- Base Tables

CREATE TABLE Airline (
    AirlineId SERIAL PRIMARY KEY,
    Airline TEXT
);

CREATE TABLE Aircraft (
    AircraftId SERIAL PRIMARY KEY,
    TailNumber TEXT,
    Manufacturer TEXT,
    Model TEXT
);

CREATE TABLE Airport (
    AirportId SERIAL PRIMARY KEY,
    AirportName TEXT,
    IataCode VARCHAR(3),
    IcaoCode VARCHAR(4),
    City TEXT,
    Country TEXT
);

CREATE TABLE Weather (
    WeatherId SERIAL PRIMARY KEY,
    AirportId INT REFERENCES Airport(AirportId),
    ObservationTime TIMESTAMP,
    Temperature FLOAT,
    WindSpeed FLOAT,
    Precipitation FLOAT
);

CREATE TABLE DelayCause (
    DelayCauseId SERIAL PRIMARY KEY,
    DelayCause TEXT
);

CREATE TABLE Flight (
    FlightId SERIAL PRIMARY KEY,
    FlightDate DATE,
    FlightNumber TEXT,
    AirlineId INT REFERENCES Airline(AirlineId),
    AirportOriginId INT REFERENCES Airport(AirportId),
    AirportDestinationId INT REFERENCES Airport(AirportId),
    AircraftId INT REFERENCES Aircraft(AircraftId),
    DepartureDelay INT
);

-- Relation Tables

CREATE TABLE FlightAircraft (
    FlightId INT REFERENCES Flight(FlightId),
    AircraftId INT REFERENCES Aircraft(AircraftId),
    PRIMARY KEY (FlightId, AircraftId)
);

CREATE TABLE FlightAirlines (
    FlightId INT REFERENCES Flight(FlightId),
    AirlineId INT REFERENCES Airline(AirlineId),
    PRIMARY KEY (FlightId, AirlineId)
);

CREATE TABLE AirportOrigin (
    FlightId INT REFERENCES Flight(FlightId),
    AirportId INT REFERENCES Airport(AirportId),
    PRIMARY KEY (FlightId, AirportId)
);

CREATE TABLE AirportDestination (
    FlightId INT REFERENCES Flight(FlightId),
    AirportId INT REFERENCES Airport(AirportId),
    PRIMARY KEY (FlightId, AirportId)
);

CREATE TABLE FlightDelay (
    FlightId INT REFERENCES Flight(FlightId),
    DelayCauseId INT REFERENCES DelayCause(DelayCauseId),
    PRIMARY KEY (FlightId, DelayCauseId)
);

-- Dummy Data

INSERT INTO Airline (Airline) VALUES
('Lufthansa'),
('Delta'),
('United'),
('Air France'),
('Emirates');

INSERT INTO Aircraft (TailNumber, Manufacturer, Model) VALUES
('D-ABCD', 'Airbus', 'A320'),
('N-12345', 'Boeing', '737'),
('F-GZCP', 'Airbus', 'A330'),
('A6-EQH', 'Boeing', '777'),
('N-67890', 'Boeing', '787');

INSERT INTO Airport (AirportName, IataCode, IcaoCode, City, Country) VALUES
('Hamburg Airport', 'HAM', 'EDDH', 'Hamburg', 'Germany'),
('JFK Airport', 'JFK', 'KJFK', 'New York', 'USA'),
('Heathrow', 'LHR', 'EGLL', 'London', 'UK'),
('CDG Airport', 'CDG', 'LFPG', 'Paris', 'France'),
('Dubai Airport', 'DXB', 'OMDB', 'Dubai', 'UAE');

INSERT INTO Weather (AirportId, ObservationTime, Temperature, WindSpeed, Precipitation) VALUES
(1, NOW(), 5.0, 20, 0.2),
(2, NOW(), 10.0, 15, 0.0),
(3, NOW(), 7.0, 25, 0.5),
(4, NOW(), 12.0, 10, 0.1),
(5, NOW(), 30.0, 5, 0.0);

INSERT INTO DelayCause (DelayCause) VALUES
('Weather'),
('Technical'),
('Crew'),
('Air Traffic'),
('Late Aircraft');

INSERT INTO Flight (FlightDate, FlightNumber, AirlineId, AirportOriginId, AirportDestinationId, AircraftId, DepartureDelay) VALUES
('2026-01-01', 'LH100', 1, 1, 2, 1, 15),
('2026-01-02', 'DL200', 2, 2, 3, 2, 5),
('2026-01-03', 'UA300', 3, 3, 4, 3, 30),
('2026-01-04', 'AF400', 4, 4, 5, 4, 0),
('2026-01-05', 'EK500', 5, 5, 1, 5, 45);

INSERT INTO FlightAircraft VALUES
(1,1),
(2,2),
(3,3),
(4,4),
(5,5);

INSERT INTO FlightAirlines VALUES
(1,1),
(2,2),
(3,3),
(4,4),
(5,5);

INSERT INTO AirportOrigin VALUES
(1,1),
(2,2),
(3,3),
(4,4),
(5,5);

INSERT INTO AirportDestination VALUES
(1,2),
(2,3),
(3,4),
(4,5),
(5,1);

INSERT INTO FlightDelay VALUES
(1,1),
(2,2),
(3,3),
(4,4),
(5,5);