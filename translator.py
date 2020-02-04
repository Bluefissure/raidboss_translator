import codecs
import json
import csv
import os
import requests
import ast
from collections import defaultdict

ffxiv_datamining_base = "https://raw.githubusercontent.com/xivapi/ffxiv-datamining/master/csv/"
ffxiv_datamining_cn_base = "https://raw.githubusercontent.com/thewakingsands/ffxiv-datamining-cn/master/"

class Translator():
	def __init__(self):
		self.db_path = "./db/"
		self.en_path = os.path.join(self.db_path, "en")
		self.cn_path = os.path.join(self.db_path, "cn")
		for path in [self.db_path, self.en_path, self.cn_path]:
			if not os.path.exists(path):
				os.makedirs(path)
		self.npc_dict = defaultdict(str)
		self.action_dict = defaultdict(str)
		self.status_dict = defaultdict(str)

	def download_res(self):
		for file in ["BNpcName.csv", "Action.csv", "Status.csv"]:
			r = requests.get(os.path.join(ffxiv_datamining_base, file))
			with codecs.open(os.path.join(self.en_path, file), "wb") as f:
				f.write(r.content)
			r = requests.get(os.path.join(ffxiv_datamining_cn_base, file))
			with codecs.open(os.path.join(self.cn_path, file), "wb") as f:
				f.write(r.content)

	def init_db(self):
		en_name_key = defaultdict(str)
		with codecs.open(os.path.join(self.en_path, "BNpcName.csv")) as f:
			reader = csv.reader(f)
			for row in reader:
				if len(row) < 4: continue
				key, single, plural = row[0], row[1], row[3]
				if not key.isdigit():
					continue
				en_name_key[single.lower()] = key
				en_name_key[plural.lower()] = key
		cn_key_name = defaultdict(str)
		with codecs.open(os.path.join(self.cn_path, "BNpcName.csv")) as f:
			reader = csv.reader(f)
			for row in reader:
				if len(row) < 4: continue
				key, single, plural = row[0], row[1], row[3]
				if not key.isdigit():
					continue
				cn_key_name[key] = single
		for k in en_name_key.keys():
			self.npc_dict[k] = cn_key_name[en_name_key[k]]

		en_name_key = defaultdict(str)
		with codecs.open(os.path.join(self.en_path, "Action.csv")) as f:
			reader = csv.reader(f)
			for row in reader:
				if len(row) < 2: continue
				key, name = row[0], row[1]
				if not key.isdigit():
					continue
				en_name_key[name.lower()] = key
		cn_key_name = defaultdict(str)
		with codecs.open(os.path.join(self.cn_path, "Action.csv")) as f:
			reader = csv.reader(f)
			for row in reader:
				if len(row) < 2: continue
				key, name = row[0], row[1]
				if not key.isdigit():
					continue
				cn_key_name[key] = name
		for k in en_name_key.keys():
			self.action_dict[k] = cn_key_name[en_name_key[k]]


		en_name_key = defaultdict(str)
		with codecs.open(os.path.join(self.en_path, "Status.csv")) as f:
			reader = csv.reader(f)
			for row in reader:
				if len(row) < 2: continue
				key, name = row[0], row[1]
				if not key.isdigit():
					continue
				en_name_key[name.lower()] = key
		cn_key_name = defaultdict(str)
		with codecs.open(os.path.join(self.cn_path, "Status.csv")) as f:
			reader = csv.reader(f)
			for row in reader:
				if len(row) < 2: continue
				key, name = row[0], row[1]
				if not key.isdigit():
					continue
				cn_key_name[key] = name
		for k in en_name_key.keys():
			self.status_dict[k] = cn_key_name[en_name_key[k]]

	def translate(self, file_path):
		with codecs.open(file_path, "r", "utf8") as file:
			to_translate = ast.literal_eval(file.read())
		for k in to_translate["replaceSync"].keys():
			to_translate["replaceSync"][k] = self.npc_dict[k.lower()]
		for k in to_translate["replaceText"].keys():
			to_translate["replaceText"][k] = self.npc_dict[k.lower()] or self.action_dict[k.lower()] or self.status_dict[k.lower()]
		with codecs.open(file_path, "w", "utf8") as file:
			json.dump(to_translate, file, indent=4)
