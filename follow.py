#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Use text editor to edit the script and type in valid Instagram username/password

from InstagramAPI import InstagramAPI
import random
import json
import time
import csv
import math
import sqlite3
import urllib
from datetime import datetime, timedelta

#TODO: read sleep time given in header of request
#TODO: tablas logs, history que guardara todos los followers y followed
#TODO: follow by near place
#TODO: follow people that liked media using getMediaLikers
#TODO: make the bot to like and follow by different algorithms (near place, different hashtags) and
#save all them and iterations somewhere. it could be db or a list in the file. I think in the db is better
#cause there if it crashes I can save it for another session, or maybe the other is better cause it changes
#always. Also I have to try to pass the data when it gives exception of type like / follow
class IgSession:
	def __init__(self,username,password,
			maxFollows=500,
			minLikes=0,maxLikes=100000,
			maxUsersToFollow = 10,
			hashtagsList = ["wonderlust","wild","nature","balance"],
			sleepingTimeFrom = 30,sleepingTimeTo = 50,
			everyXusersNotFollowedSleep = 10,
			db = 'instagram.db'):
		self.API = InstagramAPI(username,password)
		self.API.login()
		self.API.getSelfUsernameInfo()
		self.user = (self.API.LastJson)["user"]
		self.username = username
		self.pk = self.user["pk"]
		self.followerCount = self.user["follower_count"]
		self.followingCount = self.user["following_count"]
		self.minLikes = minLikes
		self.maxLikes = maxLikes
		self.maxFollows = maxFollows
		self.hashtag = self.getRandomHashtag(hashtagsList)
		self.everyXusersNotFollowedSleep = everyXusersNotFollowedSleep
		self.sleepingTimeFrom = sleepingTimeFrom
		self.sleepingTimeTo = sleepingTimeTo
		self.conn = None
		self.db = db
		self.followingTable = "FOLLOWING_USERS"
		self.followersTable = "FOLLOWERS_USERS"
		self.followedTable = "USERS_FOLLOWED"
		self.whitelistTable = "USERS_WHITELIST"
		self.logTable = "LOG"
		self.likeAction = 'LIKE'
		self.followAction = 'FOLLOW'
		self.unfollowAction = 'UNFOLLOW'
		self.maxUsersToFollow = maxUsersToFollow
		self.profilePicUrl = self.user['profile_pic_url']
		urllib.urlretrieve(self.profilePicUrl, "profile_image.jpg")
		self.createTables()

	def createTables(self):
		self.connectToDb()
		self.createTable(self.followedTable)
		self.createTable(self.followingTable)
		self.createTable(self.followersTable)
		self.createTable(self.whitelistTable)
		self.createLogTable(self.logTable)
		self.closeDbConnection()

	def deleteTable(self,table):
		query = "DROP TABLE IF EXISTS %s" % (table)
		self.execute(query)

	def createTable(self,tableName):
		self.execute("""CREATE TABLE IF NOT EXISTS {} (
		  USER_ID INTEGER PRIMARY KEY,
		  USERNAME TEXT NOT NULL,
		  FULL_NAME TEXT,
		  DATE_CREATED TEXT NOT NULL DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%S', 'NOW','localtime')),
		  UNIQUE (USERNAME))""".format(tableName))

	def createLogTable(self,tableName):
		self.execute("""CREATE TABLE IF NOT EXISTS {} (
		  IG_ACTION TEXT NOT NULL,
		  REASON TEXT,
		  ITEM_ID INTEGER,
		  USERNAME TEXT NOT NULL,
		  FULL_NAME TEXT,
		  DATE_CREATED TEXT NOT NULL DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%S', 'NOW','localtime'))
		  )""".format(tableName))

	#Le paso el username nada mas por cuestiones de que quede mas lindo, no hace falta para el like
	def like(self,mediaId,username,fullName,reason=''):
		liked = self.API.like(mediaId)
		if liked:
			self.insertLogUser(self.likeAction,reason,username,mediaId,fullName)
		return liked

	def follow(self,userId,username,fullName,reason=''):
		query = 'SELECT EXISTS (SELECT USER_ID FROM %s WHERE USERNAME = \'%s\')' % (self.followingTable,username)
		cur = self.cursorExecute(query)
		alreadyFollowing = cur.fetchone()
		if alreadyFollowing:
			followed = self.API.follow(userId)
			if followed:
				self.insertLogUser(self.followAction,reason,username,userId,fullName)
				self.insertUser(self.followedTable,username,userId,fullName)
				self.insertUser(self.followingTable,username,userId,fullName)
			return followed
		else:
			return False

	def unfollow(self,userId,username,fullName,reason=''):
		unfollowed = self.API.unfollow(userId)
		if unfollowed:
			self.insertLogUser(self.unfollowAction,reason,username,userId,fullName)
			self.deleteUserBy(self.followedTable,'USER_ID',userId)
			self.deleteUserBy(self.followingTable,'USER_ID',userId)
		return unfollowed


	def getRandomHashtag(self,hashtagsList):
		hashtag = random.choice(hashtagsList)
		print "Randomly selected #" + hashtag + " from list of hashtags" 
		return hashtag

	def setHashtag(self,hashtag):
		self.hashtag = hashtag

	def connectToDb(self):
		if(self.conn == None):
			self.conn = sqlite3.connect(self.db)
		return self.conn

	def closeDbConnection(self):
		if(self.conn != None):
			self.conn.close()
		self.conn = None

	def cursor(self):
		return self.conn.cursor()

	#Prerequisito: Estar conectado a la base de datos, asi no hay que conectarse cada vez a la base
	def insertUser(self,table,username,userId,fullName):
		query = 'INSERT OR IGNORE INTO %s (USER_ID,USERNAME,FULL_NAME) VALUES (%s,\'%s\',\'%s\')' % (table,userId,username,fullName)
		print query
		self.execute(query)

	def insertLogUser(self,action,reason,username,itemId,fullName):
		query = 'INSERT INTO %s (IG_ACTION,REASON,USERNAME,ITEM_ID,FULL_NAME) VALUES (\'%s\',\'%s\',\'%s\',%s,\'%s\')' % (self.logTable,action,reason,username,itemId,fullName)
		print query
		self.execute(query)

	def deleteUserBy(self,table,column,valueOfColumn):
		query = 'DELETE FROM %s WHERE %s=%s' % (table,column,valueOfColumn)
		print query
		self.execute(query)

	def tableUsersNumber(self,tableName):
		query = 'SELECT COUNT(*) FROM %s' % (tableName)
		self.execute(query)

	def execute(self,query):
		self.conn.execute(query)
		self.conn.commit()

	def cursorExecute(self,query):
		cur = self.cursor()
		cur.execute(query)
		return cur

	def updateDb(self,cancelar):
		self.updateFollowersDb(cancelar)
		self.updateFollowingDb(cancelar)

	def updateFollowingDb(self,cancelar):
		self.connectToDb()
		c = 0
	 	nextMaxId = ''
	 	moreUsers = True

		self.deleteTable(self.followingTable)
		self.createTable(self.followingTable)
		while c < self.followingCount and moreUsers:
			if cancelar[0]:
				cancelar[0]=False
				break
			self.API.getUserFollowings(self.pk,nextMaxId)
			followingJson = self.API.LastJson
			allUsers = followingJson["users"]
			for user in allUsers:
				if cancelar[0]:
					break
				userId = str(user["pk"])
				userUsername = user["username"]
				userFullName = user["full_name"].replace("'","''")
				self.insertUser(self.followingTable,userUsername,userId,userFullName)
				c = c+1
			try:
				nextMaxId = followingJson["next_max_id"]
			except:
				moreUsers = False
		self.closeDbConnection()

	def updateFollowersDb(self,cancelar):
		self.connectToDb()
		c = 0
	 	nextMaxId = ''
	 	moreUsers = True	
		self.deleteTable(self.followersTable)
		self.createTable(self.followersTable)
		while c < self.followerCount and moreUsers:
			if cancelar[0]:
				break
			self.API.getUserFollowers(self.pk,nextMaxId)
			followersJson = self.API.LastJson
			allUsers = followersJson["users"]
			for user in allUsers:
				if cancelar[0]:
					break
				userId = str(user["pk"])
				userUsername = user["username"]
				userFullName = user["full_name"].replace("'","''")
				self.insertUser(self.followersTable,userUsername,userId,userFullName)
				c = c+1
			try:
				nextMaxId = followersJson["next_max_id"]
			except:
				moreUsers = False
		self.closeDbConnection()

	def followBot(self,cancelar):
		self.connectToDb()
		self.createTable(self.followedTable)
		self.API.getHashtagFeed(self.hashtag)
		tags = self.API.LastJson
		follows = 0
		likes = 0
		first = True
		i = 0

		while follows < self.maxFollows:
			if cancelar[0]:
				cancelar[0]=False
				break
			
			# Agarro items
			if first:
				try:
					print "Ranked items"
					item = tags["ranked_items"][i]
					i += 1
				except:
					i = 0
					first = False
					print "Standard items"
					item = tags["items"][i]
			else:
				print "Standard items"
				try:
					i += 1
					item = tags["items"][i]
				except:
					self.API.getHashtagFeed(self.hashtag,tags["next_max_id"])
					tags = self.API.LastJson
					i = 0
					item = tags["items"][i]
			print i
			#Ya tengo prox item

			#Miro condiciones y lo sigo o no al usuario de ese item
			if (item["user"]["friendship_status"]["following"] == False ):
				userUsername = item["user"]["username"]
				query = "SELECT count(*) FROM FOLLOWING_USERS WHERE USERNAME = \'%s\'" % (userUsername)
				cursor = self.cursorExecute(query)
				alreadyFollowed = bool(cursor.fetchone()[0])
				if item["has_liked"] == False and item["like_count"] >= self.minLikes and item["like_count"] <= self.maxLikes and not alreadyFollowed:
					userId = item["user"]["pk"]
					fullName = item["user"]["full_name"].replace("'","''")

					print "Liking & following @" + userUsername + "..."
					liked=self.like(item["pk"],userUsername,fullName)
					followed=self.follow(userId,userUsername,fullName)
					if( liked ):
						likes += 1
						print "Like #" + str(likes)
					else:
						print "Could not like"
					if( followed ):
						follows += 1
						print "Follow #" + str(follows)
					else:
						print "Could not follow"

				else:
					if item["like_count"] < self.minLikes:
						print "Not enough likes"
					elif item["like_count"] > self.maxLikes:
						print "Over likes"
					elif item["has_liked"] == True:
						print "Already liked"
					elif alreadyFollowed:
						print "Already followed"
		self.closeDbConnection()

	def followByLocation(self,locationString):
		self.API.searchLocation(locationString)
		suggestedLocations = self.API.LastJson
		nextMaxId = ''
		contador = 0
		self.connectToDb()
		for location in suggestedLocations['items']:
			locationId = location['location']['pk']
			self.API.getLocationFeed(locationId,nextMaxId)
			locationFeed = self.API.LastJson
			try:
				items = locationFeed['ranked_items']
			except:
				items = locationFeed['items']
			for item in items:
				contador += 1
				# Hacer cosas aca
				# print json.dumps(item,indent=4)
				mediaId = item['pk']
				userId = item['user']['pk']
				username = item['user']['username']
				fullName = item['user']['full_name'].replace("'","''")
				reasonLike = 'Liking by location: %s' % (location['location']['name'])
				self.like(mediaId,username,fullName,reasonLike)
				reasonFollow = 'Following by location: %s' % (location['location']['name'])
				self.follow(userId, username, fullName, reasonFollow)
			try:
				nextMaxId = locationFeed['next_max_id']
			except:
				self.closeDbConnection()
				break

	def stealUserFollowers(self,usernameFromWhomSteal):
		self.API.searchUsername(usernameFromWhomSteal)
		hisPk = self.API.LastJson['user']['pk']
		nextMaxId = ''
		followed = 0
		self.connectToDb()
		while followed < self.maxUsersToFollow :
			self.API.getUserFollowers(hisPk,nextMaxId)
			search = self.API.LastJson
			hisFollowers = search['users']
			for user in hisFollowers:
				status = self.follow(user['pk'],user['username'],user['full_name'].replace("'","''"))
				if status:
					followed += 1
				if followed >= self.maxUsersToFollow:
					break
			try:
				nextMaxId = search['next_max_id']
			except:
				self.closeDbConnection()
				break

	def followMediaLikers(self,mediaId):
		self.API.getMediaLikers(mediaId)
		likers = self.API.LastJson
		followed = 0
		for liker in likers["users"]:
			if self.follow(liker["pk"],liker["username"],liker["full_name"].replace("'","''")):
				followed += 1
			if self.maxUsersToFollow == followed:
				break

	def unfollowBot(self,cancelar,days=2):
		self.connectToDb()
		today = datetime.now()
		limitDate = (today - timedelta(days)).strftime("%Y-%m-%d %H:%M:%S")
		query = "SELECT USERNAME,USER_ID,FULL_NAME FROM %s WHERE USERNAME IN (SELECT USERNAME FROM %s WHERE DATE_FOLLOWED < \'%s\') AND USERNAME NOT IN (SELECT USERNAME FROM %s)" % (self.followingTable,self.followedTable,limitDate,self.whitelistTable)
		cur = self.cursorExecute(query)
		for userUsername,userId,fullName in cur:
			if cancelar[0]:
				cancelar[0]=False
				break
			print userUsername + " is not following me and not in whitelist, now unfollowing him"
			self.unfollow(userId,userUsername,fullName.replace("'","''"))
				
		self.closeDbConnection()

	def followersCursor(self):
		self.connectToDb()
		query = "SELECT USERNAME FROM FOLLOWERS_USERS"
		cursor = self.cursorExecute(query)
		self.closeDbConnection()
		return cursor

	def logout(self):
		return self.API.logout()
########################################