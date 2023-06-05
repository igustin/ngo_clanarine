#!/usr/bin/python3.11

# moduli za pripremu i generiranje uplatnica
import jinja2
import json
import textwrap
import subprocess
import csv
import sys

# moduli za pripremu i slanje mailova
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header


def kreiraj_uplatnicu(podaci):
    """
    Prima podatke u JSON formatu i vraća sadržaj PDF datoteke
    """
    def sredi_znakove(value):
        rjecnik = {u'š': u'scaron', u'Š': u'Scaron',
                   u'ž': u'zcaron', u'Ž': u'Zcaron',
                   u'đ': u'dcroat', u'Đ': u'Dcroat',
                   u'ć': u'cacute', u'Ć': u'Cacute',
                   u'č': u'ccaron', u'Č': u'Ccaron'}

        for k, v in rjecnik.items():
            value = value.replace(k, u') show /%s glyphshow (' % v)

        return value

    jinja = jinja2.Environment(loader=jinja2.FileSystemLoader(searchpath="./"))
    jinja.filters['sredi_znakove'] = sredi_znakove

    template = jinja.get_template("uplatnica.tpl")

    podaci['opis'] = map(sredi_znakove, textwrap.wrap(podaci['opis_placanja'], 28))
    podaci['textwrap'] = textwrap

    gs = subprocess.Popen(['gs', '-sOutputFile=-', '-sDEVICE=pdfwrite',
                           '-dPDFSETTINGS=/prepress', '-dHaveTrueTypes=true',
                           '-dEmbedAllFonts=true', '-dSubsetFonts=true', '-'],
                           stdout=subprocess.PIPE, stdin=subprocess.PIPE)

    izlaz, greska = gs.communicate(template.render(podaci).encode('utf-8'))
    return izlaz


def ucitaj_podatke(datafile):
    """
    Učitava podatke za primatelje uplatnica iz tab-separated CSV datoteke u formatu:
    * 0. redak: zaglavlje, preskace se
    * Polja:
        0: redni broj
        1: ime i prezime polaznika
        2: Ulica i broj
        3: broj pošte i mjesto
        4: datum rođenja
        5: OIB
        6: e-mail adresa roditelja/staratelja kojem se šalje mail s uplatnicom
        7 i dalje: iznos uplate za određeni mjesec
    """
    result = []
    with open(datafile) as csv_file:
        csv_reader = csv.reader(csv_file)
        for row in csv_reader:
            if row[0] != '':
                result.append(row)
    return result


"""
Preuzimanje parametra za mjesec i godinu za koji se generiraju uplatnice i šalju mailovi.
Zadaje se u formatu "m/gggg" ili "m-m/gggg" koji se dalje koristi za offset odgovarajućeg stupca za iznos,
te oblikovanje opisa plaćanja na uplatnici, naziva datoteke uplatnice i oblikovanje maila.
"""
args = sys.argv
if len(args) < 2:
    print("Nedostaje mjesec m/gggg ili m-m/gggg za koji se rade uplatnice!")
    sys.exit()
else:
    mjesec = args[1]
    if "/" not in mjesec:
        print("Mjesec mora biti u formatu m/gggg ili m-m/gggg zbog poziva na broj!")
        sys.exit()
    mm, gggg = mjesec.split("/")
    if len(gggg) < 4:
        print("Mjesec mora biti u formatu m/gggg ili m-m/gggg zbog poziva na broj!")
        sys.exit()
    if "-" in mm:
        mm_od, mm_do = mm.split("-")
    else:
        mm_od, mm_do = mm, mm
    if int(mm_od) not in range(1,13) or int(mm_do) not in range(1,13) or int(mm_od) > int(mm_do):
        print("Mjesec mora biti u formatu m/gggg ili m-m/gggg zbog poziva na broj!")
        sys.exit()
    print("Radim i šaljem uplatnice za " + mm + ". mjesec " + gggg + ". godine, evidentirano kao " + mm_od + "/" + gggg)


"""
Učitavanje podataka o članovima i iznosima.
Detalji formata opisani u funkciji.
"""
uplate_polaznika = ucitaj_podatke("clanarine.csv")
"""
Offset za stupac u kojem je iznos računa
"""
for mjesec_offset in range(0,len(uplate_polaznika[0])):
    if mjesec == uplate_polaznika[0][mjesec_offset]:
        break
if mjesec_offset == len(uplate_polaznika[0])-1 and mjesec != uplate_polaznika[0][mjesec_offset]:
    print("Zadani mjesec nije pronađen u zaglavlju tablice!")
    sys.exit()


"""
Učitavanje niza predefiniranih podataka za ispunjavanje uplatnice
Podaci primatelja su fiksni, podaci primatelja varijabilni
"""
def read_config():
    cfg = {}
    with open('config.json') as f:
        cfg = json.loads(f.read())

    return cfg

cfg = read_config()
uplatnica = cfg['uplatnica']
print(uplatnica)

# predefiniranje maila za slanje
sender_email = cfg['email']['sender_email']

# autorizacija i prijava na Gmail SMTP server
smtp_server = cfg['email']['smtp_server']
smtp_port = cfg['email']['smtp_port']
username = cfg['email']['username']
password = cfg['email']['password']
smtp_connection = smtplib.SMTP(smtp_server, smtp_port)
smtp_connection.starttls()
smtp_connection.login(username, password)

def load_email_template():
    email_template = None
    try:
        with open('email.txt') as f:
            email_template = f.read()
            return email_template
    except FileNotFoundError:
        sys.stderr.write('Ne postoji email.txt predložak. Ne mogu nastaviti bez toga.\n')
        sys.exit(1)


email_template = load_email_template()

"""
Petlja koja po svakom članu čitanje njegove podatke, generira uplatnicu,
kreira i šalje mail.
"""
skip_header = True
for polaznik in uplate_polaznika:
    if skip_header:
        skip_header = False
        continue

    print("Član " + polaznik[0] + ": " + polaznik[1])

    # popunjavanje podataka uplatnice

    uplatnica['ime_i_prezime_platitelja'] = polaznik[1]
    uplatnica['ulica_i_broj_platitelja'] = polaznik[2]
    uplatnica['postanski_i_grad_platitelja'] = polaznik[3]
    iznos = polaznik[mjesec_offset].replace(",","").replace(" €","")
    if iznos == "000" or iznos == "":
        continue
    uplatnica['iznos'] = iznos
    # poziv na broj: oib-ggggmm
    poziv_na_broj = f"{polaznik[5]:0>{11}}" + "-" + gggg + f"{mm_od:0>{2}}"
    uplatnica['poziv_na_broj_primatelja'] = poziv_na_broj
    opis = "Članarina za STEM radionice " + polaznik[1] + " " + mjesec
    uplatnica['opis_placanja'] = opis

    # kreiranje i spremanje uplatnice u poddirektorij radi slanja i arhive

    pdf_uplatnica = kreiraj_uplatnicu(uplatnica)
    # naziv datoteke uplatnice: Uplatnica_imeprezime_mjesec.pdf
    pdf_uplatnica_filename = "Uplatnica_" + polaznik[1].replace(" ", "_") + "_" + mjesec.replace("/","_") + ".pdf"
    open("uplatnice/" + pdf_uplatnica_filename, 'wb').write(pdf_uplatnica)

    # priprema attachmenta
    with open("uplatnice/" + pdf_uplatnica_filename, "rb") as attachment:
        part = MIMEBase("application", "octet-stream")
        part.set_payload((attachment).read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', 'attachment', filename=Header(pdf_uplatnica_filename, 'utf-8').encode())

    # oblikovanje maila za slanje
    email_message = MIMEMultipart()
    email_message['From'] = sender_email
    email_message['To'] = polaznik[6]
    email_message['Subject'] = "Članarina za " + mjesec
    message = email_template.format(
        mjesec=mjesec,
        poziv_na_broj=poziv_na_broj,
        opis=opis,
        iznos=polaznik[mjesec_offset]
    )

    # pakiranje body + attachment
    email_message.attach(MIMEText(message, 'plain'))
    email_message.attach(part)

    # slanje maila
    smtp_connection.sendmail(sender_email, polaznik[6], email_message.as_string())


# zatvaranje Gmail SMTP konekcije
smtp_connection.quit()
print("Gotovo.")
