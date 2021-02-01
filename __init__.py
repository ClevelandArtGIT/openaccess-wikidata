'''
Interface to wikidata for the openaccess-api

This module contains the OpenAccessWikiData class, which is responsible
for configuring the pywikibot running Dominic Byrd-McDevitt's universal
import script which has been put in the _sync_wikidata_artwork method.
. This class is meant to be the interface for the rest
of the openaccess-api to interact with WikiData.
'''
import time
import datetime
import json
import re
import os
import sys
import csv
import argparse
import requests

BASE_PYWIKIBOT_DIR = 'modules/wikidata/config'
PATH_TO_WIKIDATA_CONFIGURATION_TEMPLATE = f'{BASE_PYWIKIBOT_DIR}/user-config.tmpl'
PATH_TO_WIKIDATA_CONFIGURATION_FILE = f'{BASE_PYWIKIBOT_DIR}/user-config.py'
PATH_TO_WIKIDATA_PASSWORD_TEMPLATE = f'{BASE_PYWIKIBOT_DIR}/user-password.tmpl'
PATH_TO_WIKIDATA_PASSWORD_FILE = f'{BASE_PYWIKIBOT_DIR}/user-password.py'

class OpenAccessWikiData():
    '''
    Class representing interface to Wikidata for the openaccess api.

    This class acts as the interface to wikidata for the openaccess-api.
    This class is responsible for configuring PyWikiBot and acting as a wrapper
    for Dominic Byrd McDevitt's universal import script, which has been refactored 
    into the _sync_wikidata_artwork method.
    '''

    def __init__(self, config):
        '''
        Configure wikidata and import the pywikibot module
        '''
        self.config = config
        self._configure_wikidata()
        #Once configuration is compete, import the pywikibot directory.
        #This in not done globally as the pywikibot directory cannot be
        #imported before configuration has taken place.
        #I decided to import pywikibot as an instance variable as I thought 
        #it was more readable than assigning it to a global variable after
        #global variable was declared, and I thoughy it made more sense in the 
        #context of the program where initialization
        #must take place before it can be imported.
        #Neither was very attractive, and any improvements to this code 
        #are welcome. 
        import pywikibot as __temp_pywikibot
        self.pywikibot = __temp_pywikibot

    def update_wikidata(self, artwork_json):
        '''
        Update a single artwork in wikidata given its json representation
        '''
        message, item = self._sync_wikidata_artwork(artwork_json)
        return message, item

    def batch_sync(self, artwork_json_list):
        '''
        Update a list of artworks in wikidata given their json representations
        '''
        result_list = []
        for artwork_json in artwork_json_list:
            #print(artwork_json["accession_number"])
            message, item = self._sync_wikidata_artwork(artwork_json)
            print(message)
            
            if item:
                wikidata_url = 'https://www.wikidata.org/wiki/'+re.sub(r'\W+', '', item.split(':')[1])
                if wikidata_url not in artwork_json['external_resources']['wikidata']:
                    artwork_json['external_resources']['wikidata'].append(wikidata_url)
            result_list.append(artwork_json)
        return result_list


    def _configure_wikidata(self):
        """
        Creates the necessary configuration files for the pywikibot module to run.

        This method automates the configuration processes in the pywikibot module. The files
        are written to a configuration directory and when the pywikibot module is imported 
        we change the current working directory to the location these files are stored.
        This directory change is done due to a quirk in pywikibot's design where config files 
        are searched for in the current working directory.
        """
        #Set the PYWIKIBOT_DIR environment variable 
        #so the pywikibot module knows where to look for configuration information
        #https://www.mediawiki.org/wiki/Manual:Pywikibot/user-config.py
        os.environ['PYWIKIBOT_DIR'] = BASE_PYWIKIBOT_DIR
        #create user-config file
        config_template = ''
        with open(PATH_TO_WIKIDATA_CONFIGURATION_TEMPLATE, 'r') as f:
            config_template = f.read()
        config_template = config_template.replace('WIKIDATA_USERNAME', self.config.get('username'))
        #wikidata requires the configuration file to be write only, so we need to set permissions to 
        #rwx to update file and then afterwords set permissions to r-x to make it not writeable. 
        if os.path.exists(PATH_TO_WIKIDATA_CONFIGURATION_FILE):
            os.chmod(PATH_TO_WIKIDATA_CONFIGURATION_FILE, 0o777)
        else:
            print('Creating user-config.py file...')
        with open(PATH_TO_WIKIDATA_CONFIGURATION_FILE, 'w') as f:
            f.write(config_template)
        os.chmod(PATH_TO_WIKIDATA_CONFIGURATION_FILE, 0o555)
        #create user-password file
        password_template = ''
        with open(PATH_TO_WIKIDATA_PASSWORD_TEMPLATE, 'r') as f:
            password_template = f.read()
        password_template = password_template.replace('WIKIDATA_USERNAME', self.config.get('username'))
        password_template = password_template.replace('WIKIDATA_BOT_USERNAME', self.config.get('bot_username'))
        password_template = password_template.replace('WIKIDATA_BOT_PASSWORD', self.config.get('bot_password'))
        if not os.path.exists(PATH_TO_WIKIDATA_PASSWORD_FILE):
            print('Creating user-password.py file...')
        with open(PATH_TO_WIKIDATA_PASSWORD_FILE, 'w') as f:
            f.write(password_template)


    def _sync_wikidata_artwork(self, artwork_json):
        '''
        Method for uploading an artwork's json metadata to wikidata.

        This method is Dominic Byrd-McDevitt's (dominic@byrd-mcdevitt.com) script modified 
        to take a single JSON artwork as a parameter.
        '''
        output = ""
            
        headers = {
            'User-Agent': 'Wikidata import script (https://paws.wmflabs.org/paws/user/Dominic/edit/CMA/universal_import.py; dominic@byrd-mcdevitt.com)',
        }

        #production
        is_test = False
        site = self.pywikibot.Site('wikidata', 'wikidata')
        ##test
        ## test doesn't work becaue I think CMA doesn't have the 
        ## wikidata infrastructure it has on production
        #is_test = True
        #site = pywikibot.Site('test', 'wikidata')
        repo = site.data_repository()

        ## Lookup files on Commons to add. (This code was used for adding links to pre-existing Commons files when Wikidata items were created for the first time. It is preserved in the code in case it is ever necessary again, but should not be used otherwise.)

        # def lookup(accession_number):
        #     with open('commons_files.csv', 'r') as output:
        #         data = csv.reader(output, delimiter='\t')
        #         images = []
        #         for row in data:
        #             if row[0] == accession_number:
        #                 if not row[1] in images:
        #                     images.append(row[1])
        #     return images

        # Get CMA data.
                           
        #data_files = ['cmadatadump1.json', 'cmadatadump2.json', 'cmadatadump3.json', 'cmadatadump4.json']
        artwork = artwork_json
        counter = 0
    # Define Wikidata properties.
        
        instance_prop = self.pywikibot.Claim(repo, u'P31')
        institution_prop = self.pywikibot.Claim(repo, u'P195')
        title_prop = self.pywikibot.Claim(repo, u'P1476')
        accession_number_prop = self.pywikibot.Claim(repo, u'P217')
        accession_qual_prop = self.pywikibot.Claim(repo, u'P195')
        copyright_prop = self.pywikibot.Claim(repo, u'P6216')
        determination_qual = self.pywikibot.Claim(repo, u'P459')
        url_prop = self.pywikibot.Claim(repo, u'P973')
        url_qual = self.pywikibot.Claim(repo, u'P854')
        retrieved_qual = self.pywikibot.Claim(repo, u'P813')
        license_prop = self.pywikibot.Claim(repo, u'P275')
        type_prop = self.pywikibot.Claim(repo, u'P31')
        created_prop = self.pywikibot.Claim(repo, u'P571')
        image_prop1 = self.pywikibot.Claim(repo, u'P18')
        image_prop2 = self.pywikibot.Claim(repo, u'P18')
        image_prop3 = self.pywikibot.Claim(repo, u'P18')
        image_props = [image_prop1, image_prop2, image_prop1]
        author_string_prop = self.pywikibot.Claim(repo, u'P2093')
        commons_prop = self.pywikibot.Claim(repo, u'P4765')
        author_string_qual = self.pywikibot.Claim(repo, u'P2093')
        image_url_qual = self.pywikibot.Claim(repo, u'P2699')
        format_qual = self.pywikibot.Claim(repo, u'P2701')
        title_qual = self.pywikibot.Claim(repo, u'P1476')
        license_qual = self.pywikibot.Claim(repo, u'P275')
        operator_qual = self.pywikibot.Claim(repo, u'P137')

        instance_prop.addSources([url_qual, retrieved_qual])
        institution_prop.addSources([url_qual, retrieved_qual])
        accession_number_prop.addSources([url_qual, retrieved_qual])
        title_prop.addSources([url_qual, retrieved_qual])
        url_prop.addSources([url_qual, retrieved_qual])
        copyright_prop.addSources([url_qual, retrieved_qual])
        license_prop.addSources([url_qual, retrieved_qual])
        type_prop.addSources([url_qual, retrieved_qual])
        created_prop.addSources([url_qual, retrieved_qual])
        image_prop1.addSources([url_qual, retrieved_qual])
        image_prop2.addSources([url_qual, retrieved_qual])
        image_prop3.addSources([url_qual, retrieved_qual])
        author_string_prop.addSources([url_qual, retrieved_qual])
        commons_prop.addQualifier(author_string_qual)
        commons_prop.addQualifier(title_qual)
        commons_prop.addQualifier(format_qual)
        commons_prop.addQualifier(license_qual)
        commons_prop.addQualifier(operator_qual)
        commons_prop.addQualifier(image_url_qual)
        
        item = self.pywikibot.ItemPage(repo)

        items = []
        claims = []

        # Parsing data from CMA into statements.
        institution_target = self.pywikibot.ItemPage(repo, u'Q657415')
        #this line fails on the test server...
        institution_prop.setTarget(institution_target)
        claims.append(institution_prop)
        #print(artwork)
        try:
            accession_number = artwork['accession_number']
            #print(str(counter) + ': ' + accession_number)

            accession_number_prop.setTarget(accession_number)
            accession_qual_prop.setTarget(institution_target)
            accession_number_prop.addQualifier(accession_qual_prop)
            claims.append(accession_number_prop)


        except KeyError as e:
            #print("ERROR %s"%(e))
            output += e
            return output

        url_qual.setTarget(artwork['url'])

        # Set reference access date here.
        #this line kills the entire program for whatever reason...
        now = datetime.datetime.now()
        retrieved_qual_target = self.pywikibot.WbTime(year=now.year, month=now.month, day=now.day)
        retrieved_qual.setTarget(retrieved_qual_target)
        title = artwork['title'].rstrip().lstrip().replace('\n', ' ').replace('\r', ' ')
        instance_target = self.pywikibot.ItemPage(repo, u'Q18593264')
        instance_prop.setTarget(instance_target)
        claims.append(instance_prop)

        title_target = self.pywikibot.WbMonolingualText(title, 'en')
        title_prop.setTarget(title_target)
        claims.append(title_prop)
        url_target = artwork['url']
        url_prop.setTarget(url_target)
        claims.append(url_prop)

    ##             Historical code about adding Wikimedia Commons file links.
    #             files = lookup(accession_number)
    #             if len(files) > 0:
    #                 n = 0
    #                 for commons_file in files[0:2]:
    #                     commonssite = pywikibot.Site('commons', 'commons')
    #                     imagelink = pywikibot.Link(commons_file, source=commonssite, default_namespace=6)
    #                     image = pywikibot.FilePage(imagelink)
    #                     image_props[n].setTarget(image)
    #                     claims.append(image_props[n])
    #                     n = n + 1

        if artwork['creation_date_earliest'] == artwork['creation_date_latest']:
            if artwork['creation_date_earliest']:
                created_target = self.pywikibot.WbTime(year=artwork['creation_date_earliest'])
                created_prop.setTarget(created_target)
                claims.append(created_prop)
        else:
            created_target = ''
        author_target = 'unknown artist'
        if len(artwork['creators']) > 0:
            author_target = ''
            for author in artwork['creators']:
                if author['description']:
                    author_target = author_target + ' ' + author['description'].replace('\n', ' ') + ';' 
            author_target = author_target[:-1].lstrip()
        if len(author_target) == 0:
            author_target = 'unknown artist'
        
        if artwork['share_license_status'] == 'Copyrighted':
            copyright_target = self.pywikibot.ItemPage(repo, u'Q50423863')
            copyright_prop.setTarget(copyright_target)            
        if artwork['share_license_status'] == 'CC0':
            copyright_target = self.pywikibot.ItemPage(repo, u'Q19652')
            copyright_prop.setTarget(copyright_target)

        determination_target = self.pywikibot.ItemPage(repo, u'Q61848113')
        determination_qual.setTarget(determination_target)
        try:
            copyright_prop.addQualifier(determination_qual)
        except:
            pass
        if artwork['share_license_status'] == 'Copyrighted' or artwork['share_license_status'] == 'CC0':
            claims.append(copyright_prop)

        entities = {
                    "type": {
                        "Amulets": "Q131557",
                        "Apparatus": "Q39546",
                        "Arms and Armor": "Q598227",
                        "Basketry": "Q201097",
                        "Book Binding": "Q1125338",
                        "Bound Volume": "Q571",
                        "Calligraphy": "Q22669850",
                        "Carpet": "Q163446",
                        "Ceramic": "Q13464614",
                        "Coins": "Q41207",
                        "Cosmetic Objects": "Q223557",
                        "Drawing": "Q93184",
                        "Embroidery": "Q18281",
                        "Enamel": "Q79496108",
                        "Forgery": "Q29541662",
                        "Funerary Equipment": "Q79497835",
                        "Furniture and woodwork": "Q60734095",
                        "Garment": "Q11460",
                        "Glass": "Q13180610",
                        "Glyptic": {"P2079": "Q929254"},
                        "Illumination": "Q8362",
                        "Implements": "Q39546",
                        "Inlays": {"P2079": "Q1281067"},
                        "Ivory": {"P186": "Q82001"},
                        "Jade": "Q60733799",
                        "Jewelry": "Q161439",
                        "Knitting": "Q29048022",
                        "Lace": "Q231250",
                        "Lacquer": "Q368972",
                        "Lamp": "Q368972",
                        "Leather": "Q79504355",
                        "Linoleum Block": "Q22060043",
                        "Lithographic Stone": "",
                        "Manuscript": "Q87167",
                        "Metalwork": "Q29382731",
                        "Miniature": "Q282129",
                        "Miscellaneous": "",
                        "Mixed Media": {"P136": "Q1902763"},
                        "Monotype": "Q22669635",
                        "Mosaic": "Q133067",
                        "Musical Instrument": "Q34379",
                        "Netsuke": "Q543901",
                        "Painting": "Q3305213",
                        "Photograph": "Q125191",
                        "Plaque": "Q4364339",
                        "Plate": "Q57216",
                        "Portfolio": "Q79509036",
                        "Portrait Miniature": "Q282129",
                        "Print": "Q11060274",
                        "Relief": "Q11060274",
                        "Rock crystal": {"P186": "Q2050687"},
                        "Sampler": "Q1513987",
                        "Scarabs": "Q2442735",
                        "Sculpture": "Q860861",
                        "Seals": "Q2474386",
                        "Silver": {"P186": "Q1090"},
                        "Spindle Whorl": "Q2474386",
                        "Stone": {"P186": "Q22731"},
                        "Tapestry": "Q184296",
                        "Textile": "Q28823",
                        "Time-based Media": {"P136": "Q57206278"},
                        "Tool": "Q39546",
                        "Velvet": {"P186": "Q243519"},
                        "Vessels": "Q987767",
                        "Wood": {"P186": "Q287"},
                        "Woodblock": "Q28913685"
                        }
                    }

        if isinstance(entities['type'][artwork['type']], str):
            if entities['type'][artwork['type']] != '':
                type_target = self.pywikibot.ItemPage(repo, entities['type'][artwork['type']])
                type_prop.setTarget(type_target)
                claims.append(type_prop)

        if artwork['share_license_status'] == 'CC0':
            if artwork.get('images'):
                commons_prop.setTarget(artwork['images']['print']['url'])
                image_url_qual.setTarget(url_target)
                author_string_qual.setTarget(author_target)
                format_qual.setTarget(self.pywikibot.ItemPage(repo, u'Q2195'))
                title_qual.setTarget(title_target)
                license_qual.setTarget(self.pywikibot.ItemPage(repo, u'Q6938433'))
                operator_qual.setTarget(institution_target)
                    
        if len(title) > 250:
            label = title[:250]
        else:
            label = title
                
        description = '(' + accession_number + ') ' + artwork['type'].lower() + ' by ' + author_target

        if len(description) > 250:
            description = description[:250]
        else:
            pass
        claimlist = []
        for claim in claims:
            claimlist.append(claim.toJSON())
        data = {'labels': {'en': label}, 'descriptions': {'en': 'artwork in the Cleveland Museum of Art\'s collection (%s)'%(accession_number)}, 'claims': claimlist}
        items.append((data, accession_number, label))
        item_return = None
        for newitem, accession_number, label in items:
            
    # Check for existing item.

            getcheck = requests.get('https://query.wikidata.org/sparql?query=SELECT%20DISTINCT%20%3FQid%20WHERE%20%7B%0A%20%20%3Fitem%20p%3AP217%20%3Fs%20.%0A%20%20%3Fs%20ps%3AP217%20"' + accession_number + '".%0A%20%20%3Fs%20pq%3AP195%20wd%3AQ657415%20.%0A%20%20BIND%28SUBSTR%28STR%28%3Fitem%29%2C%2032%20%29%20AS%20%3FQid%29%0A%7D &format=json', headers=headers).text

            try:
                check = json.loads(getcheck)
            except:
                #print(getcheck)
                return None

    # If no item with this accession number, create it.
        
            if len(check['results']['bindings']) == 0:

                #print(message)
                try:
                    item.editEntity(newitem, summary='Importing Cleveland Museum of Art collections to Wikidata: accession number ' + accession_number + '.')
                    time.sleep(10)
                    try:
                        item.addClaim(commons_prop, summary='Synchronizing Wikidata statement with Cleveland Museum of Art data: accession number ' + accession_number + '.')
                        message = "Uploaded: %s Item: %s"%(accession_number,str(item))
                        output += message
                        #print(str(item) + ': ' + label)
                        item_return = str(item)
                    except AttributeError as e:
                        message = "Failed to upload: %s  %s"%(accession_number, e)
                        message_explanation = "\n\tMost likely %s has a null image response field in artwork JSON"%(accession_number)
                        output += (message+message_explanation)

                        pass
                except self.pywikibot.exceptions.OtherPageSaveError as e:
                    message = "Failed to upload: %s  %s"%(accession_number, e)
                    output += message 
                    pass
                
    # If item found with this accession number, detect changes and synchronize any missing data.
                
            if len(check['results']['bindings']) == 1:
                item = self.pywikibot.ItemPage(repo, check['results']['bindings'][0]['Qid']['value'])
                getclaims = item.get()['claims']
                message = "syncing: %s label: %s"%(accession_number, str(item))
                output += message
                item_return = str(item)
                #print(message)
                try:
                    if item.get()['labels']['en'] != label:
                        item.editLabels(labels={'en': label }, summary='Synchronizing Wikidata label with Cleveland Museum of Art data: accession number ' + accession_number + '.')
                        output += '\n\tSynchronizing changes to label for ' + str(item) + ': ' + label
                        #print('Synchronizing changes to label for ' + str(item) + ': ' + label)
                except:
                    if not item.get()['labels'].get('en'):
                        item.editLabels(labels={'en': label }, summary='Synchronizing Wikidata label with Cleveland Museum of Art data: accession number ' + accession_number + '.')
                        output += '\n\tSynchronizing changes to label for ' + str(item) + ': ' + label
                        #print('Synchronizing changes to label for ' + str(item) + ': ' + label)
                try:
                    if item.get()['descriptions']['en'] != description:
                        item.editDescriptions(descriptions={'en': description }, summary='Synchronizing Wikidata description with Cleveland Museum of Art data: accession number ' + accession_number + '.')
                        output += '\n\tSynchronizing changes to description for ' + str(item) + ': ' + label
                        #print('Synchronizing changes to description for ' + str(item) + ': ' + label)
                except:
                    if not item.get()['descriptions'].get('en'):
                        item.editDescriptions(descriptions={'en': description }, summary='Synchronizing Wikidata description with Cleveland Museum of Art data: accession number ' + accession_number + '.')
                        output += '\n\tSynchronizing changes to description for ' + str(item) + ': ' + label
                        #print('Synchronizing changes to description for ' + str(item) + ': ' + label)

                clms = []
                for prop in item.get()['claims']:
                    for clm in item.toJSON()['claims'][prop]:
                        clm.pop('id', None)
                        if not clm['mainsnak'] in clms:
                            clms.append(clm['mainsnak'])
                            
                if artwork['share_license_status'] == 'CC0':
                    if artwork.get('images'):
                        if 'P18' not in item.get()['claims'].keys():
                            if 'P4765' not in item.get()['claims'].keys():
                                try:
                                    item.addClaim(commons_prop, summary='Synchronizing Wikidata statement with Cleveland Museum of Art data: accession number ' + accession_number + '.')
                                    output += '\n\tSynchronizing missing \'P4765\' claim for ' + str(item) + ': ' + label
                                    #print('Synchronizing missing \'P4765\' claim for ' + str(item) + ': ' + label)
                                except AttributeError as e:
                                    output += '\n\tFailed to synchronize claim %s'%(e)
                                    pass
                            
                for stmnt in claims:

                    stmnt_compare = stmnt.toJSON()
                    if not stmnt_compare['mainsnak'] in clms:
                        item.addClaim(stmnt, summary='Synchronizing Wikidata statement with Cleveland Museum of Art data: accession number ' + accession_number + '.')
                        output += '\n\tSynchronizing missing \'' + str(stmnt.toJSON()['mainsnak']['property'])  + '\' claim for ' + str(item) + ': ' + label
                        #print('Synchronizing missing \'' + str(stmnt.toJSON()['mainsnak']['property'])  + '\' claim for ' + str(item) + ': ' + label)
        
        return output, item_return

