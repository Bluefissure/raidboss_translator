import codecs
import json
import csv
import os
import requests
import ast
import re
from collections import defaultdict
import argparse
import traceback

ffxiv_datamining_base = "https://raw.githubusercontent.com/xivapi/ffxiv-datamining/master/csv/"
ffxiv_datamining_cn_base = "https://raw.githubusercontent.com/thewakingsands/ffxiv-datamining-cn/master/"
custom_entries = {
	"--sync--":"--sync--",
	"--reset--":"--reset--",
	"--stun--":"--击晕--",
	"Adds":"小怪",
}
custom_entries = defaultdict(str, custom_entries)

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
		self.placename_dict = defaultdict(str)

	def download_res(self):
		for file in ["BNpcName.csv", "Action.csv", "Status.csv", "PlaceName.csv"]:
			r = requests.get(os.path.join(ffxiv_datamining_base, file))
			with codecs.open(os.path.join(self.en_path, file), "wb") as f:
				f.write(r.content)
			r = requests.get(os.path.join(ffxiv_datamining_cn_base, file))
			with codecs.open(os.path.join(self.cn_path, file), "wb") as f:
				f.write(r.content)

	def init_db(self):
		en_name_key = defaultdict(list)
		with codecs.open(os.path.join(self.en_path, "BNpcName.csv"), "r", "utf8") as f:
			reader = csv.reader(f)
			for row in reader:
				if len(row) < 4: continue
				key, single, plural = row[0], row[1], row[3]
				if (not key.isdigit()) or (not single):
					continue
				en_name_key[single.lower()].append(key)
				en_name_key[plural.lower()].append(key)
		cn_key_name = defaultdict(str)
		with codecs.open(os.path.join(self.cn_path, "BNpcName.csv"), "r", "utf8") as f:
			reader = csv.reader(f)
			for row in reader:
				if len(row) < 4: continue
				key, single, plural = row[0], row[1], row[3]
				if (not key.isdigit()) or (not single):
					continue
				cn_key_name[key] = single
		for k in en_name_key.keys():
			for key in reversed(en_name_key[k]):
				self.npc_dict[k] = cn_key_name[key]
				if self.npc_dict[k]: break

		files = ["Action.csv", "Status.csv", "PlaceName.csv"]
		attrs = ["action_dict", "status_dict", "placename_dict"]
		for file_name, attr_name in zip(files, attrs):
			en_name_key = defaultdict(list)
			attr = getattr(self, attr_name)
			with codecs.open(os.path.join(self.en_path, file_name), "r", "utf8") as f:
				reader = csv.reader(f)
				for row in reader:
					if len(row) < 2: continue
					key, name = row[0], row[1]
					if (not key.isdigit()) or (not name):
						continue
					en_name_key[name.lower()].append(key)
			cn_key_name = defaultdict(str)
			with codecs.open(os.path.join(self.cn_path, file_name), "r", "utf8") as f:
				reader = csv.reader(f)
				for row in reader:
					if len(row) < 2: continue
					key, name = row[0], row[1]
					if (not key.isdigit()) or (not name):
						continue
					cn_key_name[key] = name
			for k in en_name_key.keys():
				for key in reversed(en_name_key[k]):
					attr[k] = cn_key_name[key]
					if attr[k]: break

	def translate_timeline(self, to_translate):
		for category in ["replaceSync", "replaceText", "~effectNames"]:
			for k in to_translate[category].keys():
				to_translate[category][k] = self.npc_dict[k.lower()] or \
					self.action_dict[k.lower()] or \
					self.status_dict[k.lower()] or \
					self.placename_dict[k.lower()] or \
					custom_entries[k.lower()] or \
					f"{k}(FIXME)"	
		return to_translate


def get_config():
	parser = argparse.ArgumentParser(description='Cactboss Raidboss Translator')
	parser.add_argument('-f', '--file', help='The file to be translated.')
	parser.add_argument('-e', '--export', action='store_true', help='Export the responses to response.csv')
	parser.add_argument('-rf', '--response_file', default='response.csv', help='Response file to save/load responses.')
	parser.add_argument('-ti', '--timeline', action='store_true', help='Whether to fix timeline translation.')
	parser.add_argument('-tr', '--trigger', action='store_true', help='Whether to fix trigger translation.')
	# Parse args.
	args = parser.parse_args()
	return args


def handle_timeline(t, args):
	content = ""
	cn_match = None
	final_match = None
	cn_timeline_replace = {
		"locale": "cn",
		"replaceSync": {},
		"replaceText": {},
		"~effectNames": {},
	}
	ok = True
	try:
		with codecs.open(args.file, "r", "utf8") as file:
			content = file.read()
			matches = re.finditer(r"( *){\s*['\"]locale['\"]: +['\"](\w+)['\"],(?:.*\n)*?\1},", content, re.MULTILINE)
			for m in matches:
				# print(f"{m.group(2)}:{m.start(0)},{m.end(0)}")
				sytax_json = m.group(0).replace("true", "True").replace("false", "False").replace("// FIXME", "# FIXME")
				timeline_replace = eval(sytax_json)
				if isinstance(timeline_replace, tuple):
					timeline_replace = timeline_replace[0]
				if m.group(2) == "cn":
					cn_match = m
					for category in ["replaceSync", "replaceText", "~effectNames"]:
						cn_timeline_replace[category].update(timeline_replace[category])
				else:
					for category in ["replaceSync", "replaceText", "~effectNames"]:
						if category not in timeline_replace:
							continue
						for key in timeline_replace[category]:
							if key not in cn_timeline_replace[category]:
								cn_timeline_replace[category][key] = ""
				final_match = m
		cn_translated = t.translate_timeline(cn_timeline_replace)
		# reload existing entries
		for category in ["replaceSync", "replaceText", "~effectNames"]:
			for k in cn_translated[category]:
				if k in cn_timeline_replace[category] and \
					("FIXME" in cn_translated[category][k] and \
						"FIXME" not in cn_timeline_replace[category][k]):
					cn_translated[category][k] = cn_timeline_replace[category][k]
	except Exception as e:
		ok = False
		traceback.print_exc()
	if ok:
		with codecs.open(args.file, "w", "utf8") as file:
			newline = False
			if cn_match:
				start, end = cn_match.start(0), cn_match.end(0) 
			else:
				newline = True
				start, end = final_match.end(0), final_match.end(0)
			cn_content = ("\n" if newline else "") + json.dumps(cn_translated, ensure_ascii=False, indent=4) + ","
			translated_content = content[:start] + cn_content + content[end:]
			file.write(translated_content)


def export_response(t, args):
	try:
		entries = []
		with codecs.open(args.file, "r", "utf8") as file:
			content = file.read()
			zone_name = re.search(r"(?: *)(?:zoneRegex:) {(?:(?:.*\n))*?(?:.*?cn: /\^(.*)\$/),", content, re.MULTILINE)
			zone_name = zone_name.group(1) if zone_name else ""
			matches = re.finditer(r"( *)(?:(?:info|alert|alarm)Text:|return|tts) {(?:(.*\n))*?\1}[,;]", content, re.MULTILINE)
			for m in matches:
				lineno = content[:m.start(0)].count('\n') + 1
				# print(f"line#{lineno}:")
				responces = re.finditer(r"(\w{2}): (.*),", m.group(0), re.MULTILINE)
				entry = defaultdict(str)
				entry["lineno"] = f"{os.path.basename(args.file)} {zone_name} line#{lineno}"
				for r in responces:
					# print(f"{r.group(1)}:{r.group(2)}")
					entry[r.group(1)] = r.group(2)
				entries.append(entry)
		existing_entry = set()
		if not os.path.exists(args.response_file):
			with codecs.open(args.response_file, "w", "utf-8-sig") as response_file:
				fieldnames = ['en', 'de', 'fr', 'ja', 'cn', 'ko', 'lineno']
				writer = csv.DictWriter(response_file, fieldnames=fieldnames, delimiter='\t')
				writer.writeheader()
		else:
			with codecs.open(args.response_file, "r", "utf-8-sig") as response_file:
				reader = csv.reader(response_file, delimiter='\t')
				headers = next(reader, None)
				column = {}
				for lang in headers:
					column[lang] = []
				for row in reader:
					for lang, text in zip(headers, row):
						column[lang].append(text.replace('\ufeff', ''))
				existing_entry = set(column["en"])
		# print(existing_entry)
		with codecs.open(args.response_file, "a", "utf-8-sig") as response_file:
			fieldnames = ['en', 'de', 'fr', 'ja', 'cn', 'ko', 'lineno']
			writer = csv.DictWriter(response_file, fieldnames=fieldnames, delimiter='\t')
			for entry in entries:
				if entry["en"] in existing_entry: continue
				writer.writerow(entry)
	except Exception as e:
		traceback.print_exc()

def handle_trigger(t, args):
	try:
		assert os.path.exists(args.response_file), f"Response file {args.response_file} not exists."
		english_idx = defaultdict(lambda: -1)
		column = {}
		with codecs.open(args.response_file, "r", "utf-8-sig") as response_file:
			reader = csv.reader(response_file, delimiter='\t')
			headers = next(reader, None)
			for h in headers:
				column[h] = []
			for idx, row in enumerate(reader):
				for lang, text in zip(headers, row):
					text = text.replace('\ufeff', '')	# remove bom
					column[lang].append(text)
					if lang == "en":
						english_idx[text] = idx
		translated_content = ""
		offset = 0
		with codecs.open(args.file, "r", "utf8") as file:
			content = file.read()
			matches = re.finditer(r"( *)(?:(?:info|alert|alarm)Text:|return|tts) {(?:(.*\n))*?\1}[,;]", content, re.MULTILINE)
			for m in matches:
				trigger = m.group(0)
				responces = re.finditer(r"(\w{2}): (.*),", trigger, re.MULTILINE)
				langs = ['en', 'de', 'fr', 'ja', 'cn', 'ko']
				en_text = ""
				for r in responces:
					if r.group(1) in langs:
						langs.remove(r.group(1))
					if r.group(1) == "en":
						en_text = r.group(2)
				idx = english_idx[en_text]
				# print(f"entext:{en_text} idx:{idx}")
				if idx < 0: continue
				for lang in langs:
					if column[lang][idx]:
						last_line_offset = trigger.rfind("\n") + 1
						new_lang = f"{lang}: {column[lang][idx]},\n"
						trigger = trigger[:last_line_offset] + new_lang + trigger[last_line_offset:]
				translated_content += content[offset:m.start(0)]
				offset = m.end(0)
				translated_content += trigger
				# print(f"offset:{offset}")
				# print(f"trigger:\n{trigger}")
				# print(f"translated_content:\n{translated_content}")
			translated_content += content[offset:]
		with codecs.open(args.file, "w", "utf8") as file:
			file.write(translated_content)
	except Exception as e:
		traceback.print_exc()


if __name__ == "__main__":
	args = get_config()
	t = Translator()
	t.init_db()
	if args.export:
		export_response(t, args)
	else:
		if args.timeline:
			handle_timeline(t, args)
		if args.trigger:
			handle_trigger(t, args)
		if not args.timeline and not args.trigger:
			print("Do nothing, please check with help.")