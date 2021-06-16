from flask import Flask
from flask import Flask, flash, redirect, render_template, request, session, abort, escape, url_for
import os

import RPi.GPIO as GPIO
import time
import RPi.GPIO as PWM
import threading
from picamera import PiCamera
import spidev
import requests

magnetic = 25
coil_A_1_pin = 18
coil_A_2_pin = 23
coil_B_1_pin = 24
coil_B_2_pin = 12
SERVO_PIN = 16
pirPin = 21
water_sensor = 13
co_mo = 22

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(magnetic, GPIO.IN)
GPIO.setup(coil_A_1_pin, GPIO.OUT)
GPIO.setup(coil_A_2_pin, GPIO.OUT)
GPIO.setup(coil_B_1_pin, GPIO.OUT)
GPIO.setup(coil_B_2_pin, GPIO.OUT)
GPIO.setup(SERVO_PIN, GPIO.OUT) 
servo = GPIO.PWM(SERVO_PIN, 50) 
GPIO.setup(pirPin,GPIO.IN)
GPIO.setup(pirPin, GPIO.IN, GPIO.PUD_UP)
GPIO.setup(water_sensor, GPIO.IN)
GPIO.setup(co_mo, GPIO.OUT) 

servo.start(0) 

spi = spidev.SpiDev()
spi.open(0,0)
p = GPIO.PWM(co_mo, 50)
p.start(0)


delay=0.01
steps = 50
cheak = 1
counter = 1
water_delay = 0.5
pad_channel = 0
spi.max_speed_hz = 1000000
rain_cheak = 0
input_state = False
staping_motor_ON = 1
shutter_ON = 0
pad_value = 0
app = Flask(__name__)
servo_cheak = 0
mo_down = False

def setStep (w1, w2, w3, w4):
  GPIO.output(coil_A_1_pin, w1)
  GPIO.output(coil_A_2_pin, w2)
  GPIO.output(coil_B_1_pin, w3)
  GPIO.output(coil_B_2_pin, w4)

def staping_motor():
    global staping_motor_ON
    while True:
	    if staping_motor_ON == 1 and (cheak == 0 or rain_cheak == 1):
		    setStep(1,0,1,0)
		    time.sleep(delay)
		    setStep(1,0,0,1)
		    time.sleep(delay)
		    setStep(0,1,0,1)
		    time.sleep(delay)
		    setStep(0,1,1,0)
		    time.sleep(delay)

def servo_motor():
    print("servo")
    servo.ChangeDutyCycle(12.5)
    time.sleep(1)
    servo.ChangeDutyCycle(2.5)
    time.sleep(1)
    servo.ChangeDutyCycle(12.5)
    time.sleep(1)
    servo.ChangeDutyCycle(0)
    shutter_ON = 0


def magnetic_code():
    global cheak
    global shutter_ON
    sensor_change_detect = 0
    #print("magnetic")
    try :
	    while True:
		    if GPIO.input(magnetic)==0:
			    if sensor_change_detect != 2:
				    cheak = 1
				    print(shutter_ON)
				    if shutter_ON == 1:
					    servo_motor()
					    shutter_ON = 0
				    
		    else :
			    cheak = 0
			    
			    sensor_change_detect = 2
			    
			    sensor_change_detect = 0
			    time.sleep(1)
    except Exception as ex :
	    print("error",ex);
		
def mo():
    global mo_down
    try:
	    while mo_down:
		    for i in range(10):
			    if mo_down == True:
				    p.ChangeDutyCycle(100)
				    time.sleep(1)
			    elif mo_down == False:
					    p.stop()
		    p.stop()
    except KeyboardInterrupt:
	    pass
    p.stop()

			
def camotion():
	camera = PiCamera()
	global input_state
	input_state=GPIO.input(pirPin)
	if input_state == True:
		#print("Motion detected")
		camera.start_preview()
		camera.resolution = (640, 480)
		
		for i in range(10):
			time.sleep(10)
			camera.capture('/home/pi/Desktop/image%s.jpe' % i)
			camera.stop_preview()
			camera.close()
		camera.stop_preview()
		camera.close()
	else:
		print("no motion")
		camera.close()
	time.sleep(1)

def rain():
	global rain_cheak
	while True:
		try:
			if GPIO.input(water_sensor):
				active_time = time.time()
				#print("no rain")
				#print(active_time)
				rain_cheak = 0
			else :
				active_time = time.time()
				#print("rain")
				#print(active_time)
				rain_cheak = 1	
		except KeyboardInterrupt:
			print ("\nUser Halt")
		time.sleep(1)
	
def readadc(adcnum):
	if adcnum > 7 or adcnum < 0:
		return -1
	r = spi.xfer([1, 8 + adcnum << 4, 0])
	data = ((r[1] & 3) << 8) + r[2]
	return data
	

def fsr():
    global pad_value
    global shutter_ON
    global mo_down
    

    while True:
	    try:
		    while True:
			    pad_value = readadc(pad_channel)
			    #print("--------------------------------")
			    #print("Pressure Pad Value : %d" % pad_value)
			    if pad_value>700:
				    mo_down = True
				    shutter_ON = 1
				    #camotion()
				    camera.close()
			    time.sleep(water_delay)
	    except KeyboardInterrupt:
		    pass 

@app.route('/')

def home():

    if not session.get('logged_in'):

	    return render_template('1_Login.html')

    else:
	    camera = PiCamera()
	    camera.resolution = (1024, 768)
	    
	   
	    camera.start_preview()
	    time.sleep(1)
	    camera.capture('/home/pi/good/static/exeee/image.jpe')
	    camera.stop_preview()
	    camera.close()
	    
	    return render_template('2_setting.html', image_file = 'exeee/image.jpe')



@app.route('/login', methods=['POST'])

def do_admin_login():

    if (request.form['password'] == '1234' and request.form['username'] == 'hanna') or (request.form['password'] == '1234' and request.form['username'] == 'jiwon') or (request.form['password'] == '1234' and request.form['username'] == 'gyeong'):

	    session['logged_in'] = True
	    session['username'] = request.form['username']

    else:

	    flash('wrong password!')

    return home()

 

@app.route("/logout")

def logout():

    session['logged_in'] = False

    return home()



@app.route('/option', methods=['POST'])
def option():
    if request.method == "POST":
	    option = list(request.form.values())
	    print(option)
	    if(len(option) == 1 and option[0] == "ON"):
		    session['shutter'] ="down"
		    session['window2'] ="open"
		
		
	    else:
		    if(len(option)== 2):
			    session['shutter'] = option[0]
			    session['window2'] = option[1]

			
		    elif(len(option)== 1):
			    if(option[0] == "down"):
				    session['shutter'] = option[0]
				    session['window2'] = "oop"

			    else:
				    session['window2'] = option[0]
				    session['shutter'] ="dd"
		    else:
			    session['window2'] = "oop"
			    session['shutter'] ="dd"
    return print2()        

    
def print2():
    global staping_motor_ON
    global shutter_ON
    global mo_down
	
    #win only
    if(session['window2'] == "open" and session['shutter'] != "down"):
	    staping_motor_ON = 1
	    shutter_ON = 1
	    mo_down = False
	
	
    #shu only
    elif(session['shutter'] == "down" and session['window2'] != "open"):
	    staping_motor_ON = 0
	    shutter_ON = 0
	    mo_down = True
	
    #two
    elif(session['window2'] == "open" and session['shutter'] == "down"):
	    staping_motor_ON = 1
	    shutter_ON = 1
	    mo_down = True
	
	
    elif(session['window2'] == "oop" and session['shutter'] == "dd"):
	    staping_motor_ON = 0
	    shutter_ON = 0
	    mo_down = False
	
    return security_on() 
	 
@app.route('/security_ off')
def security_off():
    global cheak
    global input_state
    global pad_value
    
    #print(input_state)
    #print(pad_value)
	
    if (input_state == True or pad_value > 700) and cheak == 1:
	    return render_template('3_em.html')
	
@app.route('/security_on')
def security_on():
	
	thread1 = threading.Thread(target = staping_motor)
	thread2 = threading.Thread(target = magnetic_code)
	thread3 = threading.Thread(target = rain)
	thread4 = threading.Thread(target = fsr)
	thread5 = threading.Thread(target = mo)
	thread6 = threading.Thread(target = security_off)

	
	
	thread1.start()		
	thread2.start()	
	thread3.start()		
	thread4.start()
	thread5.start()
	thread6.start()

	return render_template('2_setting.html')
    

if __name__ == "__main__":

    app.secret_key = os.urandom(12)

    app.run(debug=True,host='0.0.0.0', port=4000)
