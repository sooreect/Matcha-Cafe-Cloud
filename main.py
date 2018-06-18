#MatchaCafe
#2018 Tida Sooreechine


from google.appengine.api import urlfetch
from google.appengine.ext import ndb
import os
import urllib
import jinja2
import webapp2
import json
import datetime
import random
import string


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


state = ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(9)])


CLIENT_ID = '473405177390-db91oskf8ouqjl5p6vp93k1iav3hc7hu.apps.googleusercontent.com'
CLIENT_SECRET = '0HZJx5e_xgUAyhTymAt25RpF'
REDIRECT_URI = 'https://tida496final.appspot.com/oauth'


def getUserEmail(token):
	bearer_token = 'Bearer ' + token
	headers = {'Authorization': bearer_token}
	result = urlfetch.fetch(url='https://www.googleapis.com/plus/v1/people/me', method=urlfetch.GET, headers=headers)
	result_content = json.loads(result.content)
	email = result_content['emails'][0]['value']
	return email


class Customer(ndb.Model):
	id = ndb.StringProperty()
	first = ndb.StringProperty(required=True)	
	last = ndb.StringProperty()
	email = ndb.StringProperty(required=True)
	member = ndb.BooleanProperty()
	orders = ndb.StringProperty(repeated=True)


class Order(ndb.Model):
	id = ndb.StringProperty()
	customer_id = ndb.StringProperty(required=True)
	ordered_date = ndb.StringProperty()
	pickup_date = ndb.StringProperty()
	icecream_qty = ndb.IntegerProperty()	#$4 each
	latte_qty = ndb.IntegerProperty()		#$5 each
	eclair_qty = ndb.IntegerProperty()		#$3 each
	macaron_qty = ndb.IntegerProperty()		#$2 each
	total = ndb.IntegerProperty()


class CustomerHandler(webapp2.RequestHandler):
	def get(self, id=None):
		headers = self.request.headers
		if 'Authorization' in headers.keys():
			token = headers['Authorization']
			token = token.replace('Bearer ', '')
			email = getUserEmail(token)
		else:
			self.response.set_status(400)
			self.response.write('400 Bad Request\nThe headers data is not valid.')
			return
		if email: 
			if id:	
				customer = Customer.query(Customer.id == id).get()
				if customer:
					customer_dict = customer.to_dict()
					customer_dict['self'] = '/customers/' + id
					self.response.write(json.dumps(customer_dict))
				else:
					self.response.set_status(400)
					self.response.write('400 Bad Request\nCustomer ID does not exist.')
					return
			else:	
				customer_dicts = [customer.to_dict() for customer in Customer.query()]	
				for customer in customer_dicts:
					customer['self'] = '/customers/' + str(customer['id'])
				self.response.write(json.dumps(customer_dicts))
		else:
			self.response.set_status(403)
			self.response.write('403 Forbidden\nUser is not authorized by Google.')
			return

	def post(self):
		headers = self.request.headers
		if 'Authorization' in headers.keys():
			token = headers['Authorization']
			token = token.replace('Bearer ', '')
			email = getUserEmail(token)
		else:
			self.response.set_status(400)
			self.response.write('400 Bad Request\nThe headers data is not valid.')
			return
		if email: 
			data = json.loads(self.request.body)
			if 'first' not in data.keys() or data['first'] is None:
				self.response.set_status(403)
				self.response.write('403 Forbidden\nCannot create customer entry without a first name.')
				return
			customer = Customer(first = data['first'], email = email, orders = [])
			if 'last' in data.keys():
				if data['last'] is not None:
					customer.last = data['last']
			if 'member' in data.keys():
				if data['member'] is not None:
					customer.member = data['member']
			else:
				customer.member = False
			customer.put()
			customer.id = customer.key.urlsafe()	
			customer.put() 
			customer_dict = customer.to_dict()	
			customer_dict['self'] = '/customers/' + customer.key.urlsafe()
			self.response.write(json.dumps(customer_dict))
		else:
			self.response.set_status(403)
			self.response.write('403 Forbidden\nUser is not authorized by Google.')
			return

	def patch(self, id=None):
		headers = self.request.headers
		if 'Authorization' in headers.keys():
			token = headers['Authorization']
			token = token.replace('Bearer ', '')
			email = getUserEmail(token)
		else:
			self.response.set_status(400)
			self.response.write('400 Bad Request\nThe headers data is not valid.')
			return
		if email: 
			if id:
				customer = Customer.query(Customer.id == id).get()
				if customer: 
					if customer.email == email:
						data = json.loads(self.request.body)
						if 'email' in data.keys():
							self.response.set_status(403)
							self.response.write('403 Forbidden\nCannot modify customer email')
							return
						if 'orders' in data.keys():
							self.response.set_status(403)
							self.response.write('403 Forbidden\nCannot modify orders through customers')
							return
						if 'first' in data.keys():
							if data['first'] is None:
								self.response.set_status(403)
								self.response.write('403 Forbidden\nCustomer entry must have a first name.')
								return
							else:
								customer.first = data['first']
						if 'last' in data.keys():
							customer.last = data['last']
						if 'member' in data.keys():
							customer.member = data['member']
						customer.put()
						customer_dict = customer.to_dict()
						customer_dict['self'] = '/customers/' + customer.key.urlsafe()
						self.response.write(json.dumps(customer_dict))
					else:
						self.response.set_status(403)
						self.response.write('403 Forbidden\nUser is not authorized to modify other customer data.')
						return
				else:
					self.response.set_status(400)
					self.response.write('400 Bad Request\nCustomer ID does not exist.')
					return
		else:
			self.response.set_status(403)
			self.response.write('403 Forbidden\nUser is not authorized by Google.')
			return

	def delete(self, id=None):
		headers = self.request.headers
		if 'Authorization' in headers.keys():
			token = headers['Authorization']
			token = token.replace('Bearer ', '')
			email = getUserEmail(token)
		else:
			self.response.set_status(400)
			self.response.write('400 Bad Request\nThe headers data is not valid.')
			return
		if email: 
			if id:
				customer = Customer.query(Customer.id == id).get()
				if customer:
					if customer.email == email:
						if customer.orders:
							orders = Order.query(Order.customer_id == customer.id)
							for order in orders:
								order.key.delete()
						customer.key.delete()
						self.response.write('Customer successfully deleted.')
					else:
						self.response.set_status(403)
						self.response.write('403 Forbidden\nUser is not authorized to modify other customer data.')
						return
				else: 
					self.response.set_status(400)
					self.response.write('400 Bad Request\nCustomer ID does not exist.')
					return
		else:
			self.response.set_status(403)
			self.response.write('403 Forbidden\nUser is not authorized by Google.')
			return


class OrderHandler(webapp2.RequestHandler):
	def get(self, id=None):
		headers = self.request.headers
		if 'Authorization' in headers.keys():
			token = headers['Authorization']
			token = token.replace('Bearer ', '')
			email = getUserEmail(token)
		else:
			self.response.set_status(400)
			self.response.write('400 Bad Request\nThe headers data is not valid.')
			return
		if email: 
			if id:	
				order = Order.query(Order.id == id).get()
				if order:
					order_dict = order.to_dict()
					order_dict['self'] = '/orders/' + id
					self.response.write(json.dumps(order_dict))
				else:
					self.response.set_status(400)
					self.response.write('400 Bad Request\nOrder ID does not exist.')
					return
			else:	
				order_dicts = [order.to_dict() for order in Order.query()]	
				for order in order_dicts:
					order['self'] = '/orders/' + str(order['id'])
				self.response.write(json.dumps(order_dicts))
		else:
			self.response.set_status(403)
			self.response.write('403 Forbidden\nUser is not authorized by Google.')
			return
			
	def post(self):
		headers = self.request.headers
		if 'Authorization' in headers.keys():
			token = headers['Authorization']
			token = token.replace('Bearer ', '')
			email = getUserEmail(token)
		else:
			self.response.set_status(400)
			self.response.write('400 Bad Request\nThe headers data is not valid.')
			return
		if email: 
			user = Customer.query(Customer.email == email).get()
			if user:
				num_icecreams = num_lattes = num_eclairs = num_macarons = 0
				sub_icecreams = sub_lattes = sub_eclairs = sub_macarons = 0
				purchase = False
				data = json.loads(self.request.body)
				if 'customer_id' in data.keys():
					if user.id != data['customer_id']:
						self.response.set_status(403)
						self.response.write('403 Forbidden\nCannot create an order with a different customer ID.')
						return
				if 'icecream_qty' in data.keys():
					if data['icecream_qty']:
						num_icecreams = data['icecream_qty']
						sub_icecreams = 4 * num_icecreams
						purchase = True
				if 'latte_qty' in data.keys():
					if data['latte_qty']:
						num_lattes = data['latte_qty']
						sub_lattes = 5 * num_lattes
						purchase = True
				if 'eclair_qty' in data.keys():
					if data['eclair_qty']:
						num_eclairs = data['eclair_qty']
						sub_eclairs = 3 * num_eclairs
						purchase = True
				if 'macaron_qty' in data.keys():
					if data['macaron_qty']:
						num_macarons = data['macaron_qty']
						sub_macarons = 2 * num_macarons
						purchase = True
				if purchase: 
					order = Order(customer_id = user.id)
					order.put()
					order.id = order.key.urlsafe()
					order.put()
					if 'ordered_date' in data.keys() and data['ordered_date'] is not None:
						order.ordered_date = data['ordered_date']
					else:
						now = datetime.datetime.now()
						order.ordered_date = now.strftime("%m/%d/%Y")
					if 'pickup_date' in data.keys() and data['pickup_date'] is not None:
						order.pickup_date = data['pickup_date']
					else:
						now = datetime.datetime.now()
						order.pickup_date = now.strftime("%m/%d/%Y")
					order.icecream_qty = num_icecreams
					order.latte_qty = num_lattes
					order.eclair_qty = num_eclairs
					order.macaron_qty = num_macarons
					order.total = sub_icecreams + sub_lattes + sub_eclairs + sub_macarons
					order.put()
					if user.member:
						order.total = order.total - 1
						order.put()
					user.orders.append(order.id)
					user.put()
					order_dict = order.to_dict()
					order_dict['self'] = '/orders/' + order.key.urlsafe()
					self.response.write(json.dumps(order_dict))
				else:
					self.response.set_status(403)
					self.response.write('403 Forbidden\nNot a valid purchase. Purchase quantity cannot be zero.')
					return
			else:
				self.response.set_status(403)
				self.response.write('403 Forbidden\nUser is not a current customer. User needs to make a customer profile first.')
				return
		else:
			self.response.set_status(403)
			self.response.write('403 Forbidden\nUser is not authorized by Google.')
			return

	def patch(self, id=None):
		headers = self.request.headers
		if 'Authorization' in headers.keys():
			token = headers['Authorization']
			token = token.replace('Bearer ', '')
			email = getUserEmail(token)
		else:
			self.response.set_status(400)
			self.response.write('400 Bad Request\nThe headers data is not valid.')
			return
		if email: 
			user = Customer.query(Customer.email == email).get()
			if user:
				if id:
					order = Order.query(Order.id == id).get()
					if order:
						customer = Customer.query(Customer.id == order.customer_id).get()
						if user.id == customer.id:
							num_icecreams = num_lattes = num_eclairs = num_macarons = 0
							sub_icecreams = sub_lattes = sub_eclairs = sub_macarons = 0
							purchase = False
							data = json.loads(self.request.body)
							if 'total' in data.keys():
								self.response.set_status(403)
								self.response.write('403 Forbidden\nCannot edit an order total.')
								return
							if 'icecream_qty' in data.keys():
								if data['icecream_qty']:
									num_icecreams = data['icecream_qty']
									sub_icecreams = 4 * num_icecreams
									purchase = True
							else:
								if order.icecream_qty:
									num_icecreams = order.icecream_qty
									sub_icecreams = 4 * num_icecreams
									purchase = True
							if 'latte_qty' in data.keys():
								if data['latte_qty']:
									num_lattes = data['latte_qty']
									sub_lattes = 5 * num_lattes
									purchase = True
							else:
								if order.latte_qty:
									num_lattes = order.latte_qty
									sub_lattes = 5 * num_lattes
									purchase = True
							if 'eclair_qty' in data.keys():
								if data['eclair_qty']:
									num_eclairs = data['eclair_qty']
									sub_eclairs = 3 * num_eclairs
									purchase = True
							else:
								if order.eclair_qty:
									num_eclairs = order.eclair_qty
									sub_eclairs = 3 * num_eclairs
									purchase = True
							if 'macaron_qty' in data.keys():
								if data['macaron_qty']:
									num_macarons = data['macaron_qty']
									sub_macarons = 2 * num_macarons
									purchase = True
							else:
								if order.macaron_qty:
									num_macarons = order.macaron_qty
									sub_macarons = 2 * num_macarons
									purchase = True
							if purchase:
								if 'customer_id' in data.keys():
									if user.id != data['customer_id']:
										self.response.set_status(403)
										self.response.write('403 Forbidden\nUser is not authorized to change an order customer')
										return
								if 'ordered_date' in data.keys():
									order.ordered_date = data['ordered_date']
								if 'pickup_date' in data.keys():
									if data['pickup_date'] is not None:
										order.pickup_date = data['pickup_date']
									else:
										now = datetime.datetime.now()
										order.pickup_date = now.strftime("%m/%d/%Y")
								order.icecream_qty = num_icecreams
								order.latte_qty = num_lattes
								order.eclair_qty = num_eclairs
								order.macaron_qty = num_macarons
								order.total = sub_icecreams + sub_lattes + sub_eclairs + sub_macarons
								order.put()
								orderer = Customer.query(Customer.id == order.customer_id).get()
								if orderer.member:
									order.total = order.total - 1
									order.put()
								order_dict = order.to_dict()
								order_dict['self'] = '/orders/' + order.key.urlsafe()
								self.response.write(json.dumps(order_dict))
							else: 
								self.response.set_status(403)
								self.response.write('403 Forbidden\nNot a valid purchase. Purchase quantity cannot be zero.')
								return
						else:
							self.response.set_status(403)
							self.response.write('403 Forbidden\nUser is not authorized to modify other customer orders.')
							return
					else:
						self.response.set_status(400)
						self.response.write('400 Bad Request\nOrder ID does not exist.')
						return
			else: 
				self.response.set_status(403)
				self.response.write('403 Forbidden\nUser is not a current customer. User needs to make a customer profile first.')
				return
		else:
			self.response.set_status(403)
			self.response.write('403 Forbidden\nUser is not authorized by Google.')
			return

	def delete(self, id=None):
		headers = self.request.headers
		if 'Authorization' in headers.keys():
			token = headers['Authorization']
			token = token.replace('Bearer ', '')
			email = getUserEmail(token)
		else:
			self.response.set_status(400)
			self.response.write('400 Bad Request\nThe headers data is not valid.')
			return
		if email: 
			if id:
				order = Order.query(Order.id == id).get()
				if order:
					orderer = Customer.query(Customer.id == order.customer_id).get()
					if orderer.email == email:
						if order.id in orderer.orders:
							orderer.orders.remove(order.id)	
							orderer.put()
						order.key.delete()
						self.response.write('Order successfully deleted.')
					else:
						self.response.set_status(403)
						self.response.write('403 Forbidden\nUser is not authorized to delete other customer orders')
						return
				else: 
					self.response.set_status(400)
					self.response.write('400 Bad Request\nOrder ID does not exist.')
					return
		else:
			self.response.set_status(403)
			self.response.write('403 Forbidden\nUser is not authorized by Google.')
			return


class CustomerOrdersHandler(webapp2.RequestHandler):
	def get(self, id=None):
		headers = self.request.headers
		if 'Authorization' in headers.keys():
			token = headers['Authorization']
			token = token.replace('Bearer ', '')
			email = getUserEmail(token)
		else:
			self.response.set_status(400)
			self.response.write('400 Bad Request\nThe headers data is not valid.')
			return
		if email:
			if id:
				customer = Customer.query(Customer.id == id).get()
				if customer: 
					order_dicts = [order.to_dict() for order in Order.query(Order.customer_id == id)]
					for order in order_dicts:
						order['self'] = '/orders/' + str(order['id'])
					self.response.write(json.dumps(order_dicts))
				else:
					self.response.set_status(400)
					self.response.write('400 Bad Request\nCustomer ID does not exist')
					return
		else:
			self.response.set_status(403)
			self.response.write('403 Forbidden\nUser is not authorized.')
			return


class MainPage(webapp2.RequestHandler):
    def get(self):
    	url = 'https://accounts.google.com/o/oauth2/v2/auth?' + 'response_type=code' + '&client_id=' + CLIENT_ID + '&redirect_uri=' + REDIRECT_URI + '&scope=email' + '&state=' + state
    	template_values = {'url': url}
    	template = JINJA_ENVIRONMENT.get_template('index.html')
    	self.response.write(template.render(template_values))


#used for retrieving access codes via a simple front end web
class OauthHandler(webapp2.RequestHandler):
    def get(self):
        access_code = self.request.GET['code']
        returned_state = self.request.GET['state']
        if returned_state == state:
            data = {
                'code': access_code,
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
                'redirect_uri': REDIRECT_URI,
                'grant_type': 'authorization_code' 
            }
            encoded_data = urllib.urlencode(data)
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            result = urlfetch.fetch(url='https://www.googleapis.com/oauth2/v4/token', payload=encoded_data, method=urlfetch.POST, headers=headers)
            result_content = json.loads(result.content)
            access_token = result_content['access_token']
            headers = {'Authorization': "Bearer " + access_token}
            result = urlfetch.fetch(url='https://www.googleapis.com/plus/v1/people/me', method=urlfetch.GET, headers=headers)
            result_content = json.loads(result.content)
            template_values = {
                'first_name': result_content['name']['givenName'],
                'access_token': access_token
            }
            template = JINJA_ENVIRONMENT.get_template('oauth.html')
            self.response.write(template.render(template_values))        


allowed_methods = webapp2.WSGIApplication.allowed_methods
new_allowed_methods = allowed_methods.union(('PATCH',))
webapp2.WSGIApplication.allowed_methods = new_allowed_methods


app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/oauth', OauthHandler),
    ('/customers', CustomerHandler),	
    ('/customers/(.*)/orders', CustomerOrdersHandler),
    ('/customers/(.*)', CustomerHandler),
    ('/orders', OrderHandler),		
    ('/orders/(.*)', OrderHandler)
], debug=True)

