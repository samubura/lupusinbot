#librerie importate
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
import telegram
import time
import random
import os

#variabili globali utility
TOKEN = "418736265:AAHwfZPegrNyi8KgYcLfDp1oZkvSNDjZ1aU"
PORT = int(os.environ.get('PORT', '5000'))
updater = Updater(TOKEN)
dispatcher = updater.dispatcher

#stati menu handler
MENU, HELP, SETTINGS = range(3)

#variabili globali per il gioco
group_id=0
group_list=[]
player_list=[]
role_list=[]
#variabili stato gioco
role_index=0
can_join=0
night=True

#definizioni classi
class Player():
    """Player entity"""
    def __init__(self, name, chat_id, role=None, status='alive',vote=0, can_power=0,special_power=0):
        self.name = name
        self.chat_id = chat_id
        self.role = role
        self.status = status
        self.vote = vote
        self.can_power=can_power
        self.special_power=special_power

    def wake(self):
        if self.can_power==0:
            self.can_power=1

    def sleep(self):
        if self.can_power==1:
            self.can_power=0

    def end_power(self):
        self.can_power=-1

    def use_special(self):
        self.special_power=0

    def set_status(self,status):
        if status in ['alive','dead','victim']: #add here other valid status
            self.status=status
    def voted(self):
        self.voti+=1
#Definizioni poteri principali
def kill(bot,update,args):
    global player_list
    if night:
        if update.message.chat.type=='group':
            bot.send_message(chat_id=update.message.chat_id,text='Puoi usare questo comando solo come messaggio privato a @lupusinbot')
            return
        name=update.message.from_user.first_name
        if len(args)==0:
            bot.send_message(chat_id=update.message.chat_id,text='Devi scrivere il nome del giocatore che vuoi uccidere /kill <name>')
            return
        victim=args[0]
        for player in player_list:
            if player.name==name and player.role=='lupo' and player.can_power==1:
                for i in player_list:
                    if i.name==victim and i.role!='lupo':
                        i.set_status('victim')
                        bot.send_message(chat_id=update.message.chat_id,text='La vittima è stata scelta, ora torna a dormire')
                        go_sleep(bot)
                        return
                bot.send_message(chat_id=update.message.chat_id,text='Il giocatore non è nella lista')
                return
        bot.send_message(chat_id=update.message.chat_id,text='Non sei autorizzato ad usare questo comando')
    else: bot.send_message(chat_id=update.message.chat_id,text='Puoi usare questo potere solo di notte')
def burn(bot,update,args):
    global player_list
    if not night:
        if update.message.chat.type=='private':
            bot.send_message(chat_id=update.message.chat_id,text='Puoi usare questo comando solo in un gruppo con @lupusinbot')
            return
        if len(args)==0:
            bot.send_message(chat_id=update.message.chat_id,text='Devi scrivere il nome del giocatore che vuoi mandare al rogo /burn <name>')
            return
        name=update.message.from_user.first_name
        burned=args[0]
        for player in player_list:
            if player.name==name and player.can_power:
                for i in player_list:
                    if i.name==burned:
                        i.voted()
                        player.sleep()
                if player.can_power:
                    bot.send_message(chat_id=update.message.chat_id,text='Il giocatore non è nella lista')
        tot_vote=0
        for player in player_list:
            tot_vote+=player.vote
        if tot_vote>=len(player_list):
            end_day(bot)
            return
        bot.send_message(chat_id=update.message.chat_id,text='Non sei autorizzato ad usare questo comando')
    else:
        bot.send_message(chat_id=update.message.chat_id,text='Puoi usare questo comando solo di giorno')

#Altri poteri
def see(bot,update,args):
    print('ok')
    go_sleep(bot)
def save(bot,update,args):
    print('ok')
    go_sleep(bot)


#funzioni principali per il gioco
def start_match(bot):
    global role_list
    global role_index
    role_index=0
    wolf_list=[]
    i=0
    for r in role_list:
        if r=='lupo': break
        i=i+1
    if i!=0:
        role_list[i], role_list[0] = role_list[0], role_list[i] #scambio inline metto i lupi in testa
    #poi informo i lupi dei loro compagni
    for p in player_list:
        if p.role=='lupo':
            wolf_list.append(p)
        elif p.role in ['protettore','assassino']
            p.special_power=1
    if len(wolf_list)==1:
        bot.send_message(chat_id=wolf_list[0].chat_id,text='Sei un lupo solitario!')
    else:
        for player in wolf_list:
            bot.send_message(chat_id=player.chat_id,text='Membri del branco:')
            for w in wolf_list:
                if w.name!=player.name:
                    bot.send_message(chat_id=player.chat_id, text=w.name)
    awakening(bot)
def awakening(bot): #awaken only the right role
    global night
    night=True
    if role_index==0:
        bot.send_message(chat_id=group_id,text='Scende la notte sul villaggio, tutti vanno a dormire')

    role=role_list[role_index]
    if role=='lupo': bot.send_message(chat_id=group_id,text='Si svegliano i lupi.')
    elif role=='veggente': bot.send_message(chat_id=group_id,text='Si sveglia il veggente')
    elif role=='protettore': bot.send_message(chat_id=group_id,text='Si sveglia il protettore')
    #activate powers
    for player in player_list:
        if player.role==role:
            player.wake()
            bot.send_message(chat_id=player.chat_id,text='Lista persone vive:')
            for p in player_list:
                if p.status!='dead' and p.role!=role:
                    bot.send_message(chat_id=player.chat_id,text=p.name)
            if role=='lupo':
                bot.send_message(chat_id=player.chat_id,text='Puoi usare /kill <name> per scegliere chi uccidere')
            elif role=='veggente':
                bot.send_message(chat_id=player.chat_id,text='Puoi usare /see <name> per scegliere chi esaminare')
            elif role=='protettore':
                bot.send_message(chat_id=player.chat_id,text='Puoi usare /save <name> per scegliere chi salvare')
        return
def go_sleep(bot):
    global role_index
    global player_list

    role=role_list[role_index]
    if role=='lupo': bot.send_message(chat_id=group_id,text='I lupi hanno scelto la loro vittima e tornano a dormire')
    elif role=='veggente': bot.send_message(chat_id=group_id,text='Il veggente usa il suo potere e torna a dormire')
    elif role=='protettore': bot.send_message(chat_id=group_id,text='Il protettore sceglie chi salvare poi torna a dormire')
    for player in player_list:
        player.sleep()
    if role_index==len(role_list)-1:
        day(bot)
    else:
        role_index+=1
        awakening(bot)
def day(bot):
    #fase diurna
    global night
    global role_index
    role_index=0
    night=False
    bot.send_message(chat_id=group_id,text='Sorge il sole sul villaggio, si svegliano tutti...')
    for player in player_list:
        if player.status=='victim':  #kill the player
            player.set_status('dead')
            player.end_power()
            death_mex='...tutti tranne '+ player.name
            bot.send_message(chat_id=group_id,text=death_mex)

    bot.send_message(chat_id=group_id,text='I cittadini si riuniscono in piazza per decidere chi mandare al rogo.\nManda un messaggio con scritto /burn <name> per scegliere chi bruciare')
    bot.send_message(chat_id=group_id,text='Lista persone vive:')
    for p in player_list:
        p.wake()
        if p.status!='dead':
            bot.send_message(chat_id=group_id,text=p.name)
    return
def end_day(bot):
    global player_list
    m=0
    for i in range(0,len(player_list)-1):
        if player_list[i].vote>player_list[m].vote:
            m=i
    most_voted=[]
    for i in range(0,len(player_list)-1):
        if player_list[i].vote==player_list[m].vote:
            most_voted.append(i)
            player_list[i].vote=0   #reset vote
    if len(most_voted)>1:
        bot.send_message(chat_id=group_id,text='Situazione di parità')
    else:
        player=most_voted[0]
        player.set_status('dead')
        player.end_power()
        death_mex=player.name + ' è stato bruciato, tutti tornano a casa sentendosi più sicuri'
        bot.send_message(chat_id=group_id,text=death_mex)

    awakening(bot)

#Definizioni funzioni per relazionarsi con l'utente
def start(bot,update):
    if update.message.chat.type=='group':
        bot.send_message(chat_id=update.message.chat_id, text='Benvenuto in @lupusinbot puoi iniziare una partita scrivendo /newgame')
    elif update.effective_chat.type=='private' :
        bot.send_message(chat_id=update.message.chat_id, text='Benvenuto in @lupusinbot puoi aggiungerti ad una partita scrivendo /join')
    else:
        bot.send_message(chat_id=update.message.chat_id, text='Non disponi delle autorizzazioni necessarie per usare questo bot')
def newgame(bot, update):
    if update.message.chat.type=='group':
        kb = [[telegram.InlineKeyboardButton('Sì',callback_data='y'),telegram.InlineKeyboardButton('No',callback_data='n')]]
        kb_markup = telegram.InlineKeyboardMarkup(kb)
        bot.send_message(chat_id=update.message.chat_id, text='Nuova partita? Tutti i progressi attuali saranno persi', reply_markup=kb_markup)
    else:
        bot.send_message(chat_id=update.message.chat_id, text='Non puoi usare questo comando in una chat privata')
def menu(bot,update): #resetta le variabili globali
    global group_id
    global group_list
    global player_list
    global can_join
    global night_counter
    global role_list

    if update.callback_query.data=='y':
        del player_list[:]
        del role_list[:]
        del group_list[:]
        group_id=update.callback_query.message.chat_id
        group_list=bot.get_chat_administrators(group_id)
        bot.edit_message_text(chat_id=group_id, message_id=update.callback_query.message.message_id,
                         text='Ho creato un nuovo villaggio. Invia un messaggio privato a @lupusinbot con scritto /join per entrare.\nQuando tutti sono entrati scrivi /settings per impostare i ruoli')
        can_join=1
    else: bot.edit_message_text(chat_id=group_id, message_id=update.callback_query.message.message_id,
                     text='Seleziona un''opzione dal menù di aiuto')
                     _help(bot,update)
def _help(bot,update):
    kb = [
    [telegram.InlineKeyboardButton('Elenco ruoli',callback_data='ruoli'),telegram.InlineKeyboardButton('Elenco comandi',callback_data='comandi')],
    [telegram.InlineKeyboardButton('Come si gioca?',callback_data='faq')]
    ]
    kb_markup = telegram.InlineKeyboardMarkup(kb)
    bot.send_message(chat_id=update.callback_query.message.chat_id,text='Come posso aiutarti?', reply_markup=kb_markup)
def helpmenu(bot,update):
    data=update.callback_query.data
    if data=='ruoli':
        bot.send_message(chat_id=update.callback_query.message.chat_id, text='RUOLI\n[in espansione..]')
    elif data=='comandi':
        bot.send_message(chat_id=update.callback_query.message.chat_id, text='COMANDI\n[in espansione..]')
    elif data=='faq':
        bot.send_message(chat_id=update.callback_query.message.chat_id, text='COME SI GIOCA\n[in espansione..]')
def createPlayer(bot,update):
    #creating a new player
    global player_list
    global can_join

    flag=0;
    if can_join:
        if update.message.chat_id==group_id:
            bot.send_message(chat_id=group_id, text='Puoi usare /join solo come messaggio privato a @lupusinbot')
        else:
            newplayer=Player(update.message.from_user.first_name,update.message.chat_id)
             #cerco il giocatore
            for player in player_list:
                if player.name==newplayer.name and player.chat_id==newplayer.chat_id: flag=1

            if (flag):
                bot.send_message(chat_id=update.message.chat_id, text='Sei già dentro il villaggio')
            else:
                player_list.append(newplayer)
                bot.send_message(chat_id=update.message.chat_id, text='Sei entrato nel villaggio')
                jointext=update.message.from_user.first_name + ' è entrato nel villaggio'
                bot.send_message(chat_id=group_id, text= jointext)
    else:
        bot.send_message(chat_id=update.message.chat_id, text='Al momento non è possibile aggiungersi alla partita')
def set_roles(bot,update):
    global can_join
    can_join=0
    kb = [
    [telegram.InlineKeyboardButton('Lupo',callback_data='lupo'),telegram.InlineKeyboardButton('Veggente',callback_data='veggente')],
    [telegram.InlineKeyboardButton('Protettore',callback_data='protettore'),telegram.InlineKeyboardButton('Contadino',callback_data='contadino')],
    [telegram.InlineKeyboardButton('INIZIA PARTITA',callback_data='play')]
    ]
    kb_markup = telegram.InlineKeyboardMarkup(kb)
    bot.send_message(chat_id=group_id, text='Seleziona i ruoli da inserire, premi INIZIA PARTITA quando hai finito', reply_markup=kb_markup)
def ruoli(bot,update):
    global player_list
    global role_list
    role=update.callback_query.data
    i=random.randint(0,len(player_list)-1)
    c=0
    while player_list[i].role != None and c<=len(player_list):
        i=random.randint(0,len(player_list)-1)
        c+=1
    if c<=len(player_list):
        if ((role not in role_list) and (role!='contadino')):
            role_list.append(role)
        player_list[i].role=role
        message='Inserito un ' + role
        bot.send_message(chat_id=group_id, text=message)
        message='Sei un '+role
        bot.send_message(chat_id=player_list[i].chat_id, text=message)
    else:
        kb = [
        [telegram.InlineKeyboardButton('INIZIA PARTITA',callback_data='play')]
        ]
        kb_markup = telegram.InlineKeyboardMarkup(kb)
        bot.send_message(chat_id=group_id, text='Tutti i giocatori hanno un ruolo', reply_markup=kb_markup)

#gestione tutti menu a bototoni
def button_mixer(bot,update):
    data=update.callback_query.data
    if data in ['y','n']:
        menu(bot,update)
    elif data in ['lupo','veggente','protettore','contadino']:
        ruoli(bot,update)
    elif data in ['ruoli','comandi','faq']:
        menu(bot,update)
    elif data=='play': start_match(bot)


#definizioni handler di base
start=CommandHandler('start',start)
dispatcher.add_handler(start)
join=CommandHandler('join',createPlayer)
dispatcher.add_handler(join)
newgame=CommandHandler('newgame',newgame)
dispatcher.add_handler(newgame)
settings=CommandHandler('settings',set_roles)
dispatcher.add_handler(settings)
#powers
kill=CommandHandler('kill',kill,pass_args=True)
dispatcher.add_handler(kill)
see=CommandHandler('see',see,pass_args=True)
dispatcher.add_handler(see)
save=CommandHandler('save',save,pass_args=True)
dispatcher.add_handler(save)
burn=CommandHandler('burn',burn,pass_args=True)
dispatcher.add_handler(burn)
#callbackQuery
buttons=CallbackQueryHandler(button_mixer)
dispatcher.add_handler(buttons)

#corpo del programma
updater.bot.setWebhook("https://lupusinbot.herokuapp.com/" + TOKEN)
updater.start_webhook(listen="0.0.0.0",
                    port=PORT,
                    url_path=TOKEN)
updater.idle()
