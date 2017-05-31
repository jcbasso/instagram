from kivy.app import App
from kivy.uix.screenmanager import Screen, SlideTransition
import threading

class Connected(Screen):
	def loggingOut(self):
		session = self.manager.get_screen('login').session
		session.logout()
		self.manager.current = 'login'
		self.manager.get_screen('login').resetForm()
	
	def update(self):
		def updating():
			session = self.manager.get_screen('login').session
			session.updateDb()
		threading.Thread(target=updating).start()

	def follow(self):
		def following():
			session = self.manager.get_screen('login').session
			session.followBot()
		threading.Thread(target=following).start()

	def unfollow(self):
		def unfollowing():
			session = self.manager.get_screen('login').session
			session.unfollowBot(0)
		threading.Thread(target=unfollowing).start()

	def disconnect(self):
		self.manager.transition = SlideTransition(direction="right")
		threading.Thread(target=self.loggingOut).start()
