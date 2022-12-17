import PySimpleGUI as sg
import paho.mqtt.client as mqtt

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("motor/out/#")
    client.subscribe("motor/in/set_max_range")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    # print(msg.topic+": "+str(msg.payload))
    key = msg.topic.rsplit('/', 1)[1]
    curr_key = "curr_" + key
    # print("Key:",key)

    # Update slider range
    if key == "set_max_range":
        print("Updating slider range")
        new_range = int(msg.payload.decode('utf-8'))
        if new_range < 0:
            new_range = 360000
        window["input_set_pos"].update(range=(0, new_range))
    # Update corresponding element in GUI    
    elif curr_key in window.AllKeysDict:
        window[curr_key].update(msg.payload.decode('utf-8'))


sg.theme('Light Grey 2')

pos_slider = sg.Column([[sg.Text('Set target position: '), sg.Text(key='curr_set_pos')],
             [sg.Slider(range=(0, 360000), default_value=0, tick_interval=180000, orientation='horizontal', size=(40,20), enable_events=False, key='input_set_pos')],
             [sg.HSep()]])

def create_title_element(title):
    return sg.Column([[sg.Text(title, font=('Arial', 20))], [sg.HSep()]])

def create_input_element(full_name, mqtt_key_name, use_input_text=True, button_text="Send"):
    text_element = [sg.Text(full_name+(': ' if use_input_text else '')), sg.Text(key='curr_'+mqtt_key_name, visible=use_input_text)]
    input_element = [sg.Input(key='input_'+mqtt_key_name, visible=use_input_text), sg.B(button_text, key=mqtt_key_name)]
    return sg.Column([text_element, input_element, [sg.HSep()]])

def create_output_element(full_name, mqtt_key_name):
    font = ("Arial", 14)
    text_element = [sg.Text(full_name+': ', font=font), sg.Text("None", key='curr_'+mqtt_key_name, font=font, size=(20,1))]
    return sg.Column([text_element, [sg.HSep()]])

column_1_layout = [
                    [sg.Frame(title="Motor state", border_width=5, font=("Arial", 14), layout=[
                        [create_output_element("Current position", "motor_pos")],
                        [create_output_element("Current speed", "motor_speed")],
                        [create_output_element("Current current", "motor_current")],
                    ])],
                    [sg.Frame(title="Basic functions", border_width=5, font=("Arial", 14), layout=[
                        # [create_title_element("Basic functions")],
                        [pos_slider],
                        [create_input_element("Reset encoder", "reset_encoder", use_input_text=False, button_text="Reset")],
                        [create_input_element("Set maximum range", "set_max_range")],
                        [create_input_element("Set fixed speed", "set_pwm")],
                    ])],
                    [sg.B('Exit')]
                  ]
                
column_2_layout = [
                    [sg.Frame(title="PID parameters", border_width=5, font=("Arial", 14), layout=[
                        # [create_title_element("PID parameters")],
                        [create_input_element("Set Kp", "set_kp")],
                        [create_input_element("Set Kd", "set_kd")],
                        [create_input_element("Set Ki", "set_ki")],
                    ])],
                    [sg.Frame(title="Advanced parameters", border_width=5, font=("Arial", 14), layout=[
                        # [create_title_element("Advanced parameters")],
                        [create_input_element("Set PWM period (us)", "set_period_us")],
                        [create_input_element("Set smoothing coefficient", "set_smoothing")],
                        [create_input_element("Use potentiometer", "use_potentiometer")],
                    ])],
                  ]

layout = [[
          sg.Column(column_1_layout),
          sg.VSep(),
          sg.Column(column_2_layout, vertical_alignment="top"),
         ]]

window = sg.Window('Motor Interface', layout, finalize=True, font=("Arial", 12))
window['input_set_pos'].bind('<ButtonRelease-1>', '-release')

# MQTT setup
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("127.0.0.1", 1883, 60)
client.loop_start()

# Event loop for GUI
while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED or event == 'Exit':
        break
    elif event is not None:
        print("Event:", event, values)
        if event in ['set_pos', 'input_set_pos-release']:
            # change the "output" element to be the value of "input" element
            window['curr_set_pos'].update(int(values['input_set_pos']))
            client.publish('motor/in/set_pos', values['input_set_pos'])
        else:
            window['curr_'+event].update(values['input_'+event])
            client.publish('motor/in/'+event, (values['input_'+event]) if values['input_'+event] else "0")


window.close()