import RPi.GPIO as GPIO
import time
import logging
from setupLogging import setupLogging
from datetime import date, datetime, timezone
from dateutil import tz
from devices import Touch
import asyncio
from db import Database


logger = logging.getLogger("services")

class Services:
    
    async def checkFans() -> None:
        await Services.turnDevice('Fans', 'On')
            
    async def checkWindows() -> None:
        with Database() as db:
            temp = db.query_one("SELECT value, MAX(date) from readings WHERE sensor = 'TOUCH' and valueType = 'temp'")[0]
            open_temp = int(db.query_one("SELECT value from config WHERE key = 'open_window'")[0])
            close_temp = int(db.query_one("SELECT value from config WHERE key = 'close_window'")[0])

        if temp > open_temp:
            await Services.turnDevice('Windows', 'Open')
        elif temp < close_temp:
            await Services.turnDevice('Windows', 'Close')
            
    async def checkHeater() -> None:
        with Database() as db:
            temp = db.query_one("SELECT value, MAX(date) from readings WHERE sensor = 'TOUCH' and valueType = 'temp'")[0]
            on_temp = int(db.query_one("SELECT value from config WHERE key = 'heater_on'")[0])
            off_temp = int(db.query_one("SELECT value from config WHERE key = 'heater_off'")[0])
        if temp < on_temp:
            await Services.turnDevice('Heaters', 'On')
        elif temp > off_temp:
            await Services.turnDevice('Heaters', 'Off')

            
    async def checkPump():
        index = 0
        with Database() as db:
            run_for = int(db.query_one("SELECT value from config WHERE key = 'pump_run_for'")[0])
            touch = db.query_one("SELECT value, MAX(date) from readings WHERE sensor = 'TOUCH' and valueType = 'moisture'")[0]
            pump_on = int(db.query_one("SELECT value from config WHERE key = 'pump_on'")[0])
        if touch < pump_on and GPIO.input(pin) == 1:
            await Services.turnDevice('Pump', 'On')
            while touch < pump_on and index <= 19:
                index += 1
                await asyncio.sleep(run_for)
                touch, temp = await Touch.getMoistureAndTemp()
            await Services.turnDevice('Pump', 'Off')
        return run_for * index            
            
    async def checkLights() -> None:
        with Database() as db:
            sunset = datetime.strptime(db.query_one("SELECT value, MAX(date) from readings WHERE sensor = 'SUNTIME' and valueType = 'sunset'")[0], "%Y-%m-%d %H:%M:%S-%f:00")
            sunrise = datetime.strptime(db.query_one("SELECT value, MAX(date) from readings WHERE sensor = 'SUNTIME' and valueType = 'sunrise'")[0], "%Y-%m-%d %H:%M:%S-%f:00")
        if (datetime.now() > sunset.replace(tzinfo=None)):
            await Services.turnDevice('Lights', 'On')

        elif (datetime.now() < sunrise.replace(tzinfo=None)):
            await Services.turnDevice('Lights', 'On')
        elif (sunrise.replace(tzinfo=None)<datetime.now()< sunset.replace(tzinfo=None)) :
            await Services.turnDevice('Lights', 'Off')


    def checkDeviceStatus() :
        with Database() as db:
            devices = db.query("SELECT name, pin from devices")
        logger.info("Status:")
        count=0
        for device in devices:
            count+=1
            name, pin = device
            if GPIO.input(pin) == 0:
                logger.info("\t %d. %s: ON" %(count, name))
            elif GPIO.input(int(pin)) == 1:
                logger.info("\t %d. %s: OFF" %(count, name))    

    async def turnDevice(device, status)-> None:
        
        tz_east=tz.gettz('America/New York')
        action_time=datetime.now(tz_east).strftime("%Y-%m-%d %T")
        
        with Database() as db:
            pin = db.query_one("SELECT pin from devices where name = '%s'" %device)[0]
        
        if status.upper() == "ON" or status.upper() == "OPEN":
            bln = False
            val = 1
        else:
            bln = True
            val = 0
        
        if GPIO.input(pin) == val:
            logger.info("\tTurning the %s %s" %(device, status))
            GPIO.output(pin, bln)
            with Database() as db:
                db.execute('INSERT INTO actions VALUES (?, ?, ?)', (action_time, device, status))
                db.execute("UPDATE devices  SET status = '%s' WHERE name = '%s'" %(status, device))

        
        
