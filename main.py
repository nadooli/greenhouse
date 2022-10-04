import RPi.GPIO as GPIO
import time
from dateutil import tz
from datetime import date, datetime, timezone, timedelta
import logging
from setupLogging import setupLogging
from devices import Relays, Dht22, Touch, Suntime
import asyncio
from services import Services
from db import Database



async def main() -> None:
        
    setupLogging()
    logger = logging.getLogger("main")

    try:
        tz_east=tz.gettz('America/New York')
        exc_time=datetime.now(tz_east).strftime("%Y-%m-%dT%T")
        logger.info("Execution start date/time: %s" %exc_time)
        Relays.setGPIO()
        
        with Database() as db:
            loop_sec = int(db.query_one("SELECT value from config WHERE key = 'loop_sec'")[0])
            loop_min = loop_sec/60

        while True:
            logger.info("Starting the process - repeats every %d min" % loop_min)
            loop_strt_time=datetime.now(tz_east).strftime("%Y-%m-%d %T")
            logger.info ("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")

            logger.info("Time: %s" %loop_strt_time)
            
            try:
                '''Get all the sensor values asynchronously
                    1. Inside temprature sensor
                    2. Ouside temprature sensor
                    3. Soil moisture sensor
                    4. Sunrise and sunset time
                '''
                insideTempAndHumidity, outsideTempAndHumidity, soilTempAndMoisture, sunriseSunset = await asyncio.gather(
                    Dht22.getTempAndHumidity('DHT1'),
                    Dht22.getTempAndHumidity('DHT2'),
                    Touch.getMoistureAndTemp('TOUCH'),
                    Suntime.getSuntime()
                    )
                
                logger.info ("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
                
                logger.info ("Actions:")
                                
                response = await asyncio.gather(
                    Services.checkFans(),
                    Services.checkWindows(),
                    Services.checkHeater(),
                    Services.checkPump(),
                    Services.checkLights()
                    )
                
                used_time =response[3] 

                Services.checkDeviceStatus()
                
                logger.info("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
                time.sleep(loop_sec - used_time)
            
            except RuntimeError as error:
                logger.error(error.args[0])
                continue
            except Exception as error:
                #continue
                logger.error(error.args[0])
    except Exception as error:
        #dhtDevice.exit()
        raise error
    except KeyboardInterrupt:
        logger.info("Quit - Keyboard interruption")
    finally:
        GPIO.cleanup()
        logger.info("GPIO cleaned up")
    
if __name__ == "__main__":
    asyncio.run(main())
    
        