from kivy.uix.tabbedpanel import TabbedPanel
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout

from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.colorpicker import ColorWheel
from kivy.uix.colorpicker import ColorPicker
from escpos import *

from kivy.storage.jsonstore import JsonStore
from functools import partial
store = JsonStore('config.json')
__version__ = '18.02.03'
class RootWidget(FloatLayout):
	'''This the class representing your root widget.
	   By default it is inherited from BoxLayout,
	   you can use any other layout/widget depending on your usage.
	'''
	def __init__(self, **kwargs):
		self._previously_parsed_text = ''
		super(RootWidget, self).__init__(**kwargs)
		self.get_items()
		self.get_items_edit()
		self.load_settings()
		self.carousel = None
		self.number_input = 0
		self.total = 0
		self.payback = 0
		
		self.bill_dict = {}
		self.bill_items = {}
		self.name_to_update = 0
		self.name_to_delete = 0
		self.ids.kv_item_view.bind(minimum_height=self.ids.kv_item_view.setter('height'))
		self.ids.kv_bill_view.bind(minimum_height=self.ids.kv_bill_view.setter('height'))
		self.ids.kv_items_view_stats.bind(minimum_height=self.ids.kv_items_view_stats.setter('height'))
		self.ids.kv_items_view_edit.bind(minimum_height=self.ids.kv_items_view_edit.setter('height'))
		self.ids.kv_colorwheel.bind(color=self.on_color)
	def print_bon(self):
		
		for name, value in self.bill_dict.iteritems():
			store['items'][name]['sold']= store['items'][name]['sold'] + value['amount']
		store['items'] = store['items']
		
		if self.ids.kv_print_bon.active == True:
			with printer.EscposIO(printer.Network(self.ids.kv_host_adr.text, port=int(self.ids.kv_host_port.text)), autocut=False) as p:
				p.set(font='a', size='normal', align='center', bold=True)
				p.printer.set(align='center')
				for name, value in self.bill_dict.iteritems():
					if value['bon'] == True:
						for x in range(0, value['amount']):
							print x, name
							p.writelines(self.ids.kv_header_text.text, size='normal')
							p.writelines('----', size='2x')
							p.writelines(name, size='2x')
							p.writelines('----', size='2x')
							p.writelines(self.ids.kv_footer_text.text, size='normal')
							
							if x <= value['amount']:
								p.printer.cut(mode='PART')
				
				p.printer.cashdraw(2)
		
	def open_cashdraw(self):
		Printer = printer.Network("192.168.178.249")
		Printer.cashdraw(2)
		
	def get_items(self):
		if store.exists('items'):
			for name, value in sorted(store['items'].iteritems()):
				#for price, sold  in value.iteritems():
				
				print(name, value['price'], value['color'], value['bon'], value['sold'])
				self.ids.kv_item_view.add_widget(Button(text=name+'\n'+str(value['price']),size_hint_y=1, background_normal='',background_color=value['color'],on_release=partial(self.add_to_bill,name,value['color'],value['bon'],value['price'])))
				
				
				
	def get_items_edit(self):
		if store.exists('items'):
			for name, value in sorted(store['items'].iteritems()):
				self.ids.kv_items_view_edit.add_widget(Button(text=name+'\n'+str(value['price']),size_hint_y=1,background_normal='',background_color=value['color'],on_release=partial(self.load_item,name,value['price'],value['color'], value['bon'],value['sold'])))
				
			
	def add_to_bill(self, name, color, bon, price,*args):
		if self.number_input == 0:
			self.number_input = 1
		
		if name in self.bill_dict:
			self.bill_items[name].text = str(self.number_input+int(self.bill_items[name].text))
			amount = self.bill_dict[name]['amount'] + self.number_input
		else:
			self.bill_items[name] =  Button(text=str(self.number_input),size_hint_y=1, size_hint_x=0.3,on_release=partial(self.update_bill,name))
			self.ids.kv_bill_view.add_widget(self.bill_items[name])
			self.ids.kv_bill_view.add_widget(Button(text=name,size_hint_y=1,on_release=partial(self.update_bill,name)))
			amount = self.number_input
		self.bill_dict.update({name:{ 'amount': amount, 'color': color, 'bon': bon, 'price': price}}) 
		
		self.count_total()
		
		print  self.bill_dict
		self.number_input = 0
	def update_bill(self,name,*args):
		self.bill_items[name].text = str(self.number_input)
		self.bill_dict[name]['amount'] = self.number_input
		self.number_input = 0
		self.count_total()
		
	def count_total(self):
		self.total = 0
		for name, value in self.bill_dict.iteritems():
			self.total = self.total + (float(value['amount']) * float(value['price']))

			print 'AMO', self.total
		self.ids.kv_payback_view.text = '0'
		
		
		self.ids.kv_total_view.text = str(self.total)
	def cash(self):
		if self.number_input == 0:
			self.ids.kv_payback_view.text = '0'
		else:
			self.ids.kv_payback_view.text = str(self.total - self.number_input)
		self.number_input = 0
		self.print_bon()
		self.clear()
		
	def clear(self):
		self.number_input = 0
		self.total = 0
		self.payback = 0
		
		self.bill_dict = {}
		self.bill_items = {}
		self.ids.kv_bill_view.clear_widgets(children=None)
	def clear_all(self):
		self.number_input = 0
		self.total = 0
		self.payback = 0
		
		self.bill_dict = {}
		self.bill_items = {}
		self.ids.kv_bill_view.clear_widgets(children=None)
		self.ids.kv_payback_view.text = '0'
		self.ids.kv_total_view.text = '0'
	def set_input(self,number):
		new_input = str(self.number_input)+number
		self.number_input = int(new_input)
				
	def add_item(self,name,color,bon,price):
		item_dict = {'item':{}}
		self.ids.kv_items_view_edit.clear_widgets(children=None)
		self.ids.kv_item_view.clear_widgets(children=None)
		if store.exists('items'):
			item_dict = store['items']
			item_dict.update({name:{ 'price': price, 'color':color, 'bon':bon, 'sold': 0}}) 
			store['items'] = item_dict
		else:
			store['items'] = {name:{'price': price, 'color':color, 'bon':bon, 'sold': 0}}
			
		self.get_items_edit()
		self.get_items()

	def update_item(self,name,color, bon, price):
		if self.name_to_update == 0:
			pass
		else:
			sold = self.sold_to_update
			item_dict = {'item':{}}
			self.ids.kv_items_view_edit.clear_widgets(children=None)
			self.ids.kv_item_view.clear_widgets(children=None)
			if store.exists('items'):
				item_dict = store['items']
				del item_dict[self.name_to_update] 
				item_dict.update({name:{ 'price': price, 'color':color, 'bon':bon, 'sold': sold}})

				store['items'] = item_dict
			else:
				pass
				
			self.get_items_edit()
			self.get_items()
			self.name_to_update = 0

	def delete_item(self,name,color,bon,price):
		if self.name_to_delete == 0:
			pass
		else:
			item_dict = {'item':{}}
			self.ids.kv_items_view_edit.clear_widgets(children=None)
			self.ids.kv_item_view.clear_widgets(children=None)
			if store.exists('items'):
				item_dict = store['items']
				del item_dict[self.name_to_delete] 

				store['items'] = item_dict
			else:
				store['items'] = {name:{'price': price, 'color':color, 'bon':bon, 'sold': 0}}
				
			self.get_items_edit()
			self.get_items()
			self.name_to_update = 0

	def load_item(self,name,price,color,bon,sold,*args):
		self.name_to_update = name
		self.sold_to_update = sold
		self.name_to_delete = name
		self.ids.kv_item_name.text = name
		self.ids.kv_color_button.background_color = color
		self.ids.kv_bon.touch_control = None
		self.ids.kv_bon.active = bon
		
		self.ids.kv_item_price.text = str(price)
		
		
	def on_color(self, instance, value, *args):
		self.ids.kv_color_button.background_color = self.ids.kv_colorwheel.color
		print self.ids.kv_colorwheel.color


	def get_stats(self):
		sub = 0
		total = 0
		self.ids.kv_items_view_stats.clear_widgets(children=None)
		if store.exists('items'):
			for name, value in sorted(store['items'].iteritems()):
				sub = float(value['price'])*float(value['sold'])
				total = total + sub
				self.ids.kv_items_view_stats.add_widget(Button(text=name,background_color=value['color'],size_hint_y=1))
				self.ids.kv_items_view_stats.add_widget(Button(text=str(value['price']),background_color=value['color'],size_hint_y=1))
				self.ids.kv_items_view_stats.add_widget(Button(text=str(value['sold']),background_color=value['color'],size_hint_y=1))
				self.ids.kv_items_view_stats.add_widget(Button(text=str(sub),background_color=value['color'],size_hint_y=1))
		self.ids.kv_items_view_stats.add_widget(Label(text='',size_hint_y=1))
		self.ids.kv_items_view_stats.add_widget(Label(text='',size_hint_y=1))
		self.ids.kv_items_view_stats.add_widget(Label(text='',size_hint_y=1))
		self.ids.kv_items_view_stats.add_widget(Button(text='Total '+str(total),size_hint_y=1))


	def clear_stats(self):
		item_dict = {'item':{}}
		self.ids.kv_items_view_stats.clear_widgets(children=None)

		if store.exists('items'):
			for name, value in store['items'].iteritems():
				store['items'][name]['sold'] = 0
			store['items'] = store['items']
		else:
			pass
			
		self.get_stats()

	def save_settings(self):
		store['settings'] = {'host_adr': self.ids.kv_host_adr.text,
		'host_port': self.ids.kv_host_port.text, 
		'header_text': self.ids.kv_header_text.text, 
		'footer_text': self.ids.kv_footer_text.text, 
		'print_bon': self.ids.kv_print_bon.active}
	def load_settings(self):
		if store.exists('settings'):
			self.ids.kv_host_adr.text = store['settings']['host_adr']
			self.ids.kv_host_port.text = store['settings']['host_port']
			self.ids.kv_header_text.text = store['settings']['header_text']
			self.ids.kv_footer_text.text = store['settings']['footer_text']
			self.ids.kv_print_bon.active = store['settings']['print_bon']
			
		
class MainApp(App):
	'''This is the main class of your app.
	   Define any app wide entities here.
	   This class can be accessed anywhere inside the kivy app as,
	   in python::

		 app = App.get_running_app()
		 print (app.title)

	   in kv language::

		 on_release: print(app.title)
	   Name of the .kv file that is auto-loaded is derived from the name of this cass::

		 MainApp = main.kv
		 MainClass = mainclass.kv

	   The App part is auto removed and the whole name is lowercased.
	'''
	VERSION = __version__

	
	def build(self):
		'''Your app will be build from here.
		   Return your root widget here.
		'''
		self.title = 'Festleskass ' + __version__
		self.root = RootWidget()
		return self.root

	def on_pause(self):
		'''This is necessary to allow your app to be paused on mobile os.
		   refer http://kivy.org/docs/api-kivy.app.html#pause-mode .
		'''
		return True

if __name__ == '__main__':
	MainApp().run()

