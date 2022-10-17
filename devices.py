import RPi.GPIO as GPIO
import asyncio
import adafruit_dht as dht
from adafruit_seesaw.seesaw import Seesaw
from setupLogging import setupLogging
import board
from suntime import Sun, SunTimeException
from datetime import date, datetime, timezone, timedelta
from dateutil import tz
import logging
from db import Database

logger = logging.getLogger("devices")


class Relays:
    
    def setGPIO():
        try:
            logger.info("Set GPIO setmode to BCM")
            GPIO.setmode(GPIO.BCM)
            pin_list=[5,6,13,16,19,20,21,26]
            
            logger.info("Set all GPIO output Off")
            for pin in pin_list:
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, True)
            
            with Database() as db:
                db.execute("UPDATE devices SET status = 'Off'")
                
        except Exception as error:
            logger.error(error)    

class Dht22():
        
    async def getTempAndHumidity(sensor):
        try:
            tz_east=tz.gettz('America/New York')
            reading_time=datetime.now(tz_east).strftime("%Y-%m-%d %T")
            with Database() as db:
                pin = db.query_one("SELECT pin from sensors where name = '%s'" %sensor)[0]
            dhtDevice = dht.DHT22(getattr(board, pin), use_pulseio=False)
            temp_c = dhtDevice.temperature
            temp_f = round(temp_c * (9/5)+32)
            humidity = round(dhtDevice.humidity)
            with Database() as db:
                db.execute('INSERT INTO readings VALUES (?, ?, ?, ?)', (reading_time, sensor, temp_f, "temp"))
                db.execute('INSERT INTO readings VALUES (?, ?, ?, ?)', (reading_time, sensor, humidity, "humidity"))
            if sensor == 'DHT1':
                logger.info("Inside:")
                logger.info("\t Temp: \t\t{0}F".format(temp_f))
                logger.info("\t Humidity: \t{}% ".format(humidity))
            else:
                logger.info("Outside:")
                logger.info("\t Temp: \t\t{0}F".format(temp_f))
                logger.info("\t Humidity: \t{}% ".format(humidity))
            
            with Database() as db:
                db.execute("UPDATE sensors SET status = 'Good' WHERE name = '%s'" %sensor)
                
            return [temp_f, humidity]

        except Exception as error:
                logger.error("Exception: %s" %error.args[0])
                with Database() as db:
                    db.execute("UPDATE sensors SET status = 'Error' WHERE name = '%s'" %sensor)
                    db.execute('INSERT INTO sensor_status VALUES (?, ?, ?, ?)', (reading_time, sensor, "error", error.args[0]))
                dhtDevice.exit()
        except RuntimeError as error:
                logger.error("RuntimeError: %s" %error.args[0])

class Touch():
    
    async def getMoistureAndTemp(sensor):
        
        try:
            tz_east=tz.gettz('America/New York')
            reading_time=datetime.now(tz_east).strftime("%Y-%m-%d %T")
            
            i2c_bus = board.I2C()
            ss = Seesaw(i2c_bus, addr=0x36)
            touch = ss.moisture_read()
            soil_temp_c = ss.get_temp()
            soil_temp_f = soil_temp_c * (9/5)+32
            temp = round(soil_temp_f)
            
            with Database() as db:
                db.execute('INSERT INTO readings VALUES (?, ?, ?, ?)', (reading_time, sensor, temp, "temp"))
                db.execute('INSERT INTO readings VALUES (?, ?, ?, ?)', (reading_time, sensor, touch, "moisture"))
                db.execute("UPDATE sensors SET status = 'Good' WHERE name = '%s'" %sensor)
            
            logger.info("Soil:")
            logger.info("\tTemp: \t\t{0}F".format(temp))
            logger.info ("\tMoisture: \t%s" %str(touch))
            
            return [touch, soil_temp_f]
        
        except Exception as error:
            logger.error(error.args[0])
            with Database() as db:
                db.execute("UPDATE sensors SET status = 'Error' WHERE name = '%s'" %sensor)
                db.execute('INSERT INTO sensor_status VALUES (?, ?, ?, ?)', (reading_time, sensor, "error", error.args[0]))

class Suntime():
    
    async def getSuntime():
        
        try:
            with Database() as db:
                max_date = db.query_one("SELECT MAX(date) from readings WHERE sensor = 'SUNTIME' and valueType = 'sunrise'")[0]
                latitude = float(db.query_one("SELECT value from config where key = 'latitude'")[0])
                longitude = float(db.query_one("SELECT value from config where key = 'longitude'")[0])
            if max_date is None:
                max_date = '2020-01-01 12:00:01'
            max_date = datetime.strptime(max_date, "%Y-%m-%d %H:%M:%S")
            if max_date.date() < datetime.now().date():
            
                tz_east=tz.gettz('America/New York')
                reading_time=datetime.now(tz_east).strftime("%Y-%m-%d %T")       

                sun = Sun(latitude, longitude)
                sunrise = sun.get_local_sunrise_time()
                sunset = sun.get_local_sunset_time()
                
                with Database() as db:
                    db.execute('INSERT INTO readings VALUES (?, ?, ?, ?)', (reading_time, "SUNTIME", sunrise, "sunrise"))
                    db.execute('INSERT INTO readings VALUES (?, ?, ?, ?)', (reading_time, "SUNTIME", sunset, "sunset"))
                                
                logger.info('Sunrise: %s' %sunrise)
                logger.info('Sunset: %s' %sunset)
                
                return [sunrise, sunset]
        
        except Exception as error:
            logger.error(error.args[0])
