from kivy.uix.screenmanager import Screen, SlideTransition
import threading

cancelar = [False]
class Connected(Screen):
	def loggingOut(self):
		session = self.manager.get_screen('login').session
		session.logout()
		self.manager.current = 'login'
		self.manager.get_screen('login').resetForm()
	
	def update(self):
		def updating():
			session = self.manager.get_screen('login').session
			session.updateDb(cancelar)
		threading.Thread(target=updating).start()

	def follow(self):
		def following():
			session = self.manager.get_screen('login').session
			session.followBot(cancelar)
		threading.Thread(target=following).start()

	def unfollow(self):
		def unfollowing():
			session = self.manager.get_screen('login').session
			session.unfollowBot(cancelar,0)
		threading.Thread(target=unfollowing).start()

	def cancel(self):
		cancelar[0] = True
		print cancelar[0]

	def disconnect(self):
		self.manager.transition = SlideTransition(direction="right")
		threading.Thread(target=self.loggingOut).start()
