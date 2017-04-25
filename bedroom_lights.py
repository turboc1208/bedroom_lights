import my_appapi as appapi
             
class bedroom_lights(appapi.my_appapi):

  def initialize(self):
    # self.LOGLEVEL="DEBUG"
    self.log("bedroom_lights App")

    self.hi_temp=75
    self.lo_temp=68

    self.targets={"light.sam_light_switch":{"triggers":{"light.sam_light_switch":{"type":"light","bit":64,"onValue":"on"},
                                                        "device_tracker.scox0129_sc0129":{"type":"tracker","bit":2,"onValue":"home"},
                                                        "media_player.sam_directv":{"type":"media","bit":16,"onValue":"playing"},
                                                        "sensor.sam_motion":{"type":"motion","bit":4,"onValue":8},
                                                        "input_boolean.samishomeoverride":{"type":"override","bit":1,"onValue":"on"}},
                                            "type":"light",
                                            "onState":[66,68,70,74,76,78,83,84,86,90,92,94,98,100,102,106,108,110,114,116,118,122,124,126],
                                            "dimState":[82,84,86,90,92,94,114,116,118,122,124,126],
                                            "offState":[72,80,88,96,104,112,120]+list(range(0,65)),
                                            "callback":self.light_state_handler},
                 "light.sam_fan_switch":{"triggers":{"light.sam_fan_switch":{"type":"fan","bit":32,"onValue":"on"},
                                                     "sensor.sam_temperature":{"type":"temperature","bit":8,"onValue":self.check_temp},
                                                     "input_boolean.samishomeoverride":{"type":"override","bit":1,"onValue":"on"},
                                                     "device_tracker.scox0129_sc0129":{"type":"tracker","bit":2,"onValue":"home"}},
                                         "type":"fan",
                                         "onState":[8,10,12,14,18,20,22,26,28,30,34,36,38,40,42,44,46,50,52,54,56,58,60,62,72,74,78,88,90,92,94,104,106,108,110,120,122,124,126],
                                         "dimState":[0],
                                         "offState":[0,2,4,6,16,23,32,48,64,66,68,70,80,82,84,86,96,98,100,102,112,113,116,118],
                                         "callback":self.fan_state_handler}}

    self.log("self.targets={}".format(self.targets))

    for ent in self.targets:
      for ent_trigger in self.targets[ent]["triggers"]:
        self.log("registering callback for {} on {} for target {}".format(ent_trigger,self.targets[ent]["callback"],ent))
        self.listen_state(self.targets[ent]["callback"],ent_trigger,target=ent)
      if self.targets[ent]["type"]=="light":
        self.process_light_state(ent)
      else:
        self.process_fan_state(ent)
    

  def light_state_handler(self,trigger,attr,old,new,kwargs):
    self.log("trigger = {}, attr={}, old={}, new={}, kwargs={}".format(trigger,attr,old,new,kwargs))
    self.process_light_state(kwargs["target"])

  def process_light_state(self,target,**kwargs):
    light_max=50
    light_dim=25
    # build current state binary flag.
    state=0
    type_bits={}
    for trigger in self.targets[target]["triggers"]:
      self.log("trigger={} type={} onValue={} bit={}".format(trigger,self.targets[target]["triggers"][trigger]["type"],self.targets[target]["triggers"][trigger]["onValue"],
                                                      self.targets[target]["triggers"][trigger]["bit"]))
      state=state | (self.targets[target]["triggers"][trigger]["bit"] if (self.get_state(trigger)==self.targets[target]["triggers"][trigger]["onValue"]) else 0)
      type_bits[self.targets[target]["triggers"][trigger]["type"]]=self.targets[target]["triggers"][trigger]["bit"]


    self.log("state={}".format(state))
    if not state & type_bits["override"]:
      if state in self.targets[target]["offState"]:     # these states always result in light being turned off
        self.log("state = {} turning off light".format(state))
        self.turn_off(target)
      elif state in self.targets[target]["onState"]:    # these states always result in light being turned on.
        self.log("state = {} turning on light".format(state))
        if state in self.targets[target]["dimState"]:                      # when turning on lights, media player determines whether to dim or not.
          self.log("media player involved so dim lights")
          self.turn_on(target,brightness=light_dim)
        else:
          self.log("state={} turning on light".format(state))
          self.turn_on(target,brightness=light_max)
    else:
      self.log("home override set so no automations performed")


  def fan_state_handler(self,trigger,attr,old,new,kwargs):
    self.log("trigger = {}, attr={}, old={}, new={}, kwargs={}".format(trigger,attr,old,new,kwargs))
    self.process_fan_state(kwargs["target"])

  def process_fan_state(self,target,**kwargs):
    new_state=int(float(self.get_state("sensor.office_sensor_temperature_11_1")))
    self.log("new_state={} - {} - {}".format(new_state,self.get_state("sensor.office_sensor_temperature_11_1"),target))
    if new_state>=75:
      self.log("turning on {}".format(target))
      self.turn_on(target,brightness=128)
    elif new_state<70:
      self.log("turning off {}".format(target))
      self.turn_off(target)
    else:
      self.log("new_state={} - {}".format(new_state,type(new_state)))

  def check_temp(self,fan,thermo):
    current_temp=int(float(self.get_state(thermo,attribute="temperature")))
    self.log("current_temp={}".format(current_temp))
    if current_temp>hi_temp:
      self.log("turning on fan")
      self.turn_on(fan)
    if current_temp<low_temp:
      self.log("turning off fan")
      self.turn_off(fan)
  
