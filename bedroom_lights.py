import my_appapi as appapi
             
class bedroom_lights(appapi.my_appapi):

  def initialize(self):
    # self.LOGLEVEL="DEBUG"
    self.log("bedroom_lights App")

    ######################### Values to move to config file or somewhere.
    self.light_max=254
    self.light_dim=128

    self.hi_temp=75
    self.lo_temp=68

    self.targets={"ight.sam_room_light_level":{"triggers":{"light.sam_room_light_level":{"type":"light","bit":64,"onValue":"on"},
                                                        "device_tracker.scox0129_sc0129":{"type":"tracker","bit":2,"onValue":"home"},
                                                        "media_player.sam_directv":{"type":"media","bit":16,"onValue":"playing"},
                                                        "sensor.sam_motion":{"type":"motion","bit":4,"onValue":8},
                                                        "input_boolean.samishomeoverride":{"type":"override","bit":1,"onValue":"on"}},
                                            "type":"light",
                                            "onState":[66,68,70,74,76,78,83,84,86,90,92,94,98,100,102,106,108,110,114,116,118,122,124,126],
                                            "dimState":[82,84,86,90,92,94,114,116,118,122,124,126],
                                            "offState":[72,80,88,96,104,112,120]+list(range(0,65)),
                                            "callback":self.light_state_handler},
                 "fan.sam_room_fan_level":{"triggers":{"fan.sam_room_fan_level":{"type":"fan","bit":32,"onValue":"on"},
                                                     "sensor.sam_temperature":{"type":"temperature","bit":8,"onValue":"on"},
                                                     "input_boolean.samishomeoverride":{"type":"override","bit":1,"onValue":"on"},
                                                     "device_tracker.scox0129_sc0129":{"type":"tracker","bit":2,"onValue":"home"}},
                                         "type":"fan",
                                         "onState":[8,10,12,14,18,20,22,26,28,30,34,36,38,40,42,44,46,50,52,54,56,58,60,62,72,74,78,88,90,92,94,104,106,108,110,120,122,124,126],
                                         "dimState":[0],
                                         "offState":[0,2,4,6,16,23,32,48,64,66,68,70,80,82,84,86,96,98,100,102,112,113,116,118],
                                         "callback":self.light_state_handler}}

    #################End of values to move to config file or somewhere.

    for ent in self.targets:
      for ent_trigger in self.targets[ent]["triggers"]:
        self.log("registering callback for {} on {} for target {}".format(ent_trigger,self.targets[ent]["callback"],ent))
        self.listen_state(self.targets[ent]["callback"],ent_trigger,target=ent)
      self.process_light_state(ent)      # process each light as we register a callback for it's triggers rather than wait for a trigger to fire first.


  ########
  #
  # state change handler.  All it does is call process_light_state all the work is done there.
  #
  def light_state_handler(self,trigger,attr,old,new,kwargs):
    self.log("trigger = {}, attr={}, old={}, new={}, kwargs={}".format(trigger,attr,old,new,kwargs))
    self.process_light_state(kwargs["target"])


  ########
  #
  # process_light_state.  All the light processing happens in here.
  #
  def process_light_state(self,target,**kwargs):
    # build current state binary flag.
    state=0
    type_bits={}
    
    # here we are building a binary flag/mask that represents the current state of the triggers that impact our target light.
    # one bit for each trigger.
    # bits are assigned in targets dictionary.

    for trigger in self.targets[target]["triggers"]:      # loop through triggers
      self.log("trigger={} type={} onValue={} bit={} currentstate={}".format(trigger,self.targets[target]["triggers"][trigger]["type"],self.targets[target]["triggers"][trigger]["onValue"],
                                                      self.targets[target]["triggers"][trigger]["bit"],self.normalize_state(target,trigger,self.get_state(trigger))))
      # or value for this trigger to existing state bits.
      state=state | (self.targets[target]["triggers"][trigger]["bit"] if (self.normalize_state(target,trigger,self.get_state(trigger))==self.targets[target]["triggers"][trigger]["onValue"]) else 0)

      # typebits is a quick access array that takes the friendly type of the trigger and associates it with it's bit
      # it's just to make it easier to search later.
      type_bits[self.targets[target]["triggers"][trigger]["type"]]=self.targets[target]["triggers"][trigger]["bit"]


    self.log("state={}".format(state))
    if not state & type_bits["override"]:               # if the override bit is set, then don't evaluate anything else.  Think of it as manual mode.
      if state in self.targets[target]["offState"]:     # these states always result in light being turned off
        self.log("state = {} turning off light".format(state))
        self.turn_off(target)
      elif state in self.targets[target]["onState"]:    # these states always result in light being turned on.
        self.log("state = {} turning on light".format(state))
        if state in self.targets[target]["dimState"]:                      # when turning on lights, media player determines whether to dim or not.
          self.log("media player involved so dim lights")
          self.turn_on(target,brightness=self.light_dim)
        else:                                                   # it wasn't a media player dim situation so it's just a simple turn on the light.
          self.log("state={} turning on light".format(state))
          self.turn_on(target,brightness=self.light_max)
    else:
      self.log("home override set so no automations performed")

  #############
  #
  # normalize_state - take incoming states and convert any that are calculated to on/off values.
  #
  def normalize_state(self,target,trigger,newstate):
    if newstate==None:                   # handle a newstate of none, typically means the object didn't exist.
      newstate=self.get_state(target)    # if thats the case, just return the state of the target so nothing changes.

    if type(newstate)==str:                          # deal with a new state that's a string
      if newstate in ["home","house","Home","House"]:  # deal with having multiple versions of house and home to account for.
        newstate="home"
    else:                                            # if it's not a string, we are assuming it's a number.  May not be true, but for now it should be.
      if self.targets[target]["triggers"][trigger]["type"]=="temperature":     # is it a temperature.
        currenttemp = int(float(newstate))           # convert floating point to integer.
        if currenttemp>=hi_temp:                     # handle temp Hi / Low state setting to on/off.  
          newstate="on"
        elif currenttemp<=self.low_temp:
          newstate="off"
        else:
          newstate= self.get_state(target)              # If new state is in between target points, just return current state of target so nothing changes.
      else:                                          # we have a number, but it's not a temperature so leave the value alone.
        self.log("newstate is a number, but not a temperature, so leave it alone : {}".format(newstate))
    return newstate
