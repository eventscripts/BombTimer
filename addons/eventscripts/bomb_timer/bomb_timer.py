#import EventScripts
import es
#import Libraries
import gamethread
import cfglib
import cmdlib
import langlib
import playerlib
import settinglib
import usermsg
import time

# Addon Information
info = es.AddonInfo()
info.name           = "Bomb Timer"
info.version        = "4.0.2"
info.author         = "Hunter"
info.url            = "http://addons.eventscripts.com/addons/user/289"
info.description    = "C4 Bomb Timer that counts down to explosion"
info.basename       = "bomb_timer"

hunter_bomb_timer_ver      = info.version
hunter_bomb_timer_text     = 'Hunters '+info.name+', www.sourceplugins.de, '+info.version+', ES 2.1.1.338+'

# Server Variables
bomb_timer_config          = cfglib.AddonCFG('%s/bomb_timer.cfg' % es.getAddonPath('bomb_timer'))
bomb_timer_savetime        = bomb_timer_config.cvar('bomb_timer_savetime', 30, 'How much days should inactive users be stored, before their settings get deleted? ( default = 30 )')
bomb_timer_soundload       = bomb_timer_config.cvar('bomb_timer_soundload', 1, 'Should the sounds be downloaded with EventScripts?')
bomb_timer_endannounce     = bomb_timer_config.cvar('bomb_timer_endannounce', 1, 'Should BOMB DEFUSED or BOMB EXPLODED be annouced at the end of a round?')
bomb_timer_middle_screen   = bomb_timer_config.cvar('bomb_timer_middle_screen', 1, 'Should the bomb timer be shown in the middle of the screen? ( 0 = off | 1 = HudHint | 2 = CenterMsg )')
bomb_timer_default_display = bomb_timer_config.cvar('bomb_timer_default_display', 1, 'Default settings for new connecting players')
bomb_timer_default_text    = bomb_timer_config.cvar('bomb_timer_default_text', 1, 'Default settings for new connecting players')
bomb_timer_default_sound   = bomb_timer_config.cvar('bomb_timer_default_sound', 1, 'Default settings for new connecting players')
bomb_timer_config.write()

# Language Strings
bomb_timer_ini             = cfglib.AddonINI('%s/bomb_timer.ini' % es.getAddonPath('bomb_timer'))
bomb_timer_ini.addGroup('text_E')
bomb_timer_ini.addValueToGroup('text_E', 'en', '#greenBomb exploded.')
bomb_timer_ini.addValueToGroup('text_E', 'de', '#greenBombe ist explodiert.')
bomb_timer_ini.addGroup('text_D')
bomb_timer_ini.addValueToGroup('text_D', 'en', '#greenBomb defused.')
bomb_timer_ini.addValueToGroup('text_D', 'de', '#greenBombe wurde entschaerft.')
bomb_timer_ini.addGroup('text_P')
bomb_timer_ini.addValueToGroup('text_P', 'en', '#greenBomb planted.')
bomb_timer_ini.addValueToGroup('text_P', 'de', '#greenBombe wurde gelegt.')
for x in [30, 20, 10, 5]:
    bomb_timer_ini.addGroup('text_%d'%x)
    bomb_timer_ini.addValueToGroup('text_%d'%x, 'en', '#green%d seconds to explosion.'%x)
    bomb_timer_ini.addValueToGroup('text_%d'%x, 'de', '#green%d Sekunden bis zur Explosion.'%x)
for x in [30, 20, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]:
    bomb_timer_ini.addGroup('sound_%d'%x)
    bomb_timer_ini.addValueToGroup('sound_%d'%x, 'spec', 'bombtimer/%dsec.mp3'%x)
    bomb_timer_ini.addValueToGroup('sound_%d'%x, 't', 'bombtimer/%dsec.mp3'%x)
    bomb_timer_ini.addValueToGroup('sound_%d'%x, 'ct', 'bombtimer/%dsec.mp3'%x)
bomb_timer_ini.write()

# Global Variables
bomb_timer_mp_c4timer      = es.ServerVar('mp_c4timer')
bomb_timer_language        = langlib.Strings('%s/bomb_timer.ini' % es.getAddonPath('bomb_timer'))

# Settinglib Object
bomb_timer_setting         = settinglib.create('bombtimer', 'Bomb Timer', 'toggle')

def load():
    public = es.ServerVar('hu_bt', info.version, info.name)
    public.makepublic()
    
    cmdlib.registerSayCommand('!bombtimer', _say_cmd, 'Bomb Timer')

    bomb_timer_config.execute()
    bomb_timer_setting.addoption('display', 'Display')
    bomb_timer_setting.addoption('text', 'Text')
    bomb_timer_setting.addoption('sound', 'Sound')
    bomb_timer_setting.setdefault('display', int(bomb_timer_default_display))
    bomb_timer_setting.setdefault('text', int(bomb_timer_default_text))
    bomb_timer_setting.setdefault('sound', int(bomb_timer_default_sound))
    bomb_timer_setting.addsound('ui/buttonclick.wav')

    es.log(hunter_bomb_timer_text)
    es.msg('#multi', '#green[BombTimer] #defaultLoaded')
    
def unload():
    gamethread.cancelDelayed('bomb_timer')

    cmdlib.unregisterSayCommand('!bombtimer')

    es.msg('#multi', '#green[BombTimer] #defaultUnloaded')
    
def es_map_start(event_var):
    bomb_timer_setting.clear(int(bomb_timer_savetime)*86400)
    if int(bomb_timer_soundload):
        for keyname in bomb_timer_language.keys():
            if keyname.startswith('sound_'):
                for soundname in bomb_timer_language[keyname].keys():
                    es.stringtable('downloadables', 'sound/%s'%bomb_timer_language[keyname][soundname])

def es_client_command(event_var):
    if (str(event_var['command']) == '!hunter_bomb_timer_ver') or (str(event_var['command']) == '!hunter_all_ver'):
        es.cexec(int(event_var['userid']), 'echo '+hunter_bomb_timer_text)

def player_activate(event_var):
    bomb_timer_setting.updateTime(int(event_var['userid']))
    gamethread.delayed(30, es.cexec, (int(event_var['userid']), 'echo '+hunter_bomb_timer_text))
    gamethread.delayed(15, es.tell, (int(event_var['userid']), '#multi', '#green[BombTimer] #defaultSay \'!bombtimer\' for settings menu'))

def player_disconnect(event_var):
    bomb_timer_setting.updateTime(int(event_var['userid']))

def bomb_planted(event_var):
    gamethread.delayedname(1, 'bomb_timer', bomb_ticker, (int(time.time())))
    _run_bomb('P')

def bomb_defused(event_var):
    if int(bomb_timer_endannounce):
        _run_bomb('D')

def bomb_exploded(event_var):
    if int(bomb_timer_endannounce):
        _run_bomb('E')

def bomb_ticker(tick):
    gamethread.delayedname(1, 'bomb_timer', bomb_ticker, (tick))
    _run_bomb(str(int(bomb_timer_mp_c4timer) - int(int(time.time()) - tick)))

def round_start(event_var):
    gamethread.cancelDelayed('bomb_timer')

def round_end(event_var):
    gamethread.cancelDelayed('bomb_timer')

def _say_cmd(userid, args):
    bomb_timer_setting.send(userid)

def _run_bomb(tick):
    if tick.isdigit():
        soundtext = '%s sec'%tick
    elif tick == 'P':
        soundtext = 'Bomb Planted'
    elif tick == 'D':
        soundtext = 'Bomb Defused'
    elif tick == 'E':
        soundtext = 'Bomb Exploded'
    if 'command_%s'%tick in bomb_timer_language.keys():
        for commandname in bomb_timer_language['command_%s'%tick].keys():
            es.server.queuecmd(bomb_timer_language['command_%s'%tick][commandname].strip())
    for userid in playerlib.getUseridList('#human'):
        if bomb_timer_setting.get('display', userid):
            if int(bomb_timer_middle_screen) == 1:
                usermsg.hudhint(userid, soundtext)
            elif int(bomb_timer_middle_screen) == 2:
                usermsg.centermsg(userid, soundtext)
        if bomb_timer_setting.get('text', userid):
            if 'text_%s'%tick in bomb_timer_language.keys():
                es.tell(userid, '#multi', bomb_timer_language('text_%s'%tick, {}, playerlib.getPlayer(userid).get('lang')))
        if bomb_timer_setting.get('sound', userid):
            if int(es.getplayerteam(userid)) < 2:
                keyname = 'spec'
            elif int(es.getplayerteam(userid)) == 2:
                keyname = 't'
            elif int(es.getplayerteam(userid)) == 3:
                keyname = 'ct'
            if 'sound_%s'%tick in bomb_timer_language.keys():
                es.playsound(userid, bomb_timer_language['sound_%s'%tick][keyname], 1.0)
