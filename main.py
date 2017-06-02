from kivy.app import App
from kivy.properties import StringProperty
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from follow import IgSession
import os
import threading
import sys

from connected import Connected
from notConnected import NotConnected
import atexit

class Login(Screen):
    def logging(self,username,password):
        app = App.get_running_app()
        self.session = IgSession(username,password)
        app.profilePicUrl = self.session.profilePicUrl
        print app.profilePicUrl
        # print Connected.ids
        app.session = self.session
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = 'connected'

    def do_login(self, loginText, passwordText):
        app = App.get_running_app()

        app.username = loginText
        app.password = passwordText

        threading.Thread(target=self.logging, args=(loginText,passwordText)).start()

        app.config.read(app.get_application_config())
        app.config.write()

    def resetForm(self):
        self.ids['login'].text = ""
        self.ids['password'].text = ""

class LoginApp(App):
    username = StringProperty(None)
    password = StringProperty(None)
    profilePicUrl = StringProperty(None)

    def build(self):
        manager = ScreenManager()

        manager.add_widget(Login(name='login'))
        manager.add_widget(Connected(name='connected'))
        manager.add_widget(NotConnected(name='notConnected'))

        return manager

    def get_application_config(self):
        if(not self.username):
            return super(LoginApp, self).get_application_config()

        conf_directory = self.user_data_dir + '/' + self.username

        if(not os.path.exists(conf_directory)):
            os.makedirs(conf_directory)

        return super(LoginApp, self).get_application_config(
            '%s/config.cfg' % (conf_directory)
        )

if __name__ == '__main__':
    LoginApp().run()
