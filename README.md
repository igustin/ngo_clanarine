# ngo_clanarine

ngo_clanarine je Python program za kreiranje i mailanje uplatnica za članarine udruga ili sličnu svrhu.

# Opis

Program je napravljen za potrebe jedne udruge, s raznim specifičnostima koje su bile potrebne, ali je primjenjiva i za druge udruge i slične potrebe. Značajke ovog rješenja:
* ulazni podaci se pripremaju u GoogleSheet, LibreOffice Calc, Microsoft Excel ili sličnoj tablici prema formatu opisanim u nastavku, pri čemu pojedini članovi mogu imati različite iznose (ovisno o tipu članstva, broju sudjelovanju na radionicama i slično)
* podaci se iz tablice ručno eksportiraju u CSV datoteku i koriste u programu
* program se poziva uz navođenje mjeseca (ili razdoblja) i godine za koje se šalju uplatnice
* program generira individualiziranu HUB-3 uplatnicu s 2D barkodom za plaćanje fotonalogom i trajno je sprema u poddirektorij, pri tome se poziv na broj formira u obliku OIB-GGGGMM
* program generira individualizirani mail s uputama za više načina plaćanja i PDF uplatnicom u attachmentu
* automatski šalje mail preko GMaila

# Priprema ulaznih podataka

Ulazni podaci pripremaju se u bilo kojem tabličnom kalkulatoru. Format tablice vidi se na screenshotu (izmišljeni podaci generirani ChatGPT-om). Prvi redak je zaglavlje, a ostali redovi sadrže konkretne podatke. Stupci tablice:

0) redni broj zapisa - nema posebnu funkciju, osim što se ispisuje na ekranu tijekom generiranja i slanja kako bi se pratio rad skripte
1) ime i prezime polaznika (stavlja se na uplatnicu i u sadržaj maila)
2) ulica i broj (stavlja se na uplatnicu i u sadržaj maila)
3) broj pošte i mjesto (stavlja se na uplatnicu i u sadržaj maila)
4) datum rođenja (nigdje se se koristi, ali služi evidenciji članstva sukladno Zakonu o udrugama)
5) OIB (koristi se za poziv na broj na uplatnici i evidenciji članstva sukladno Zakonu o udrugama)
6) e-mail adresa člana/roditelja/staratelja kojem se šalje mail s uplatnicom
7) i dalje - iznos uplate za određeni mjesec ili razdoblje u formatu m/gggg ili m-m/gggg, npr. 9/2022, 10/2022, 11-12/2022 i slično; ovaj format zapisa u zaglavlju je bitan jer po tome odabire stupac s iznosima, oblikuje opis plaćanja i poziv na broj

![image](https://github.com/igustin/ngo_clanarine/assets/1834262/16241c9d-7548-4fd5-9bb8-271f3397fbb2)

# Konfiguriranje programa

Prije prve upotrebe, program treba unutar izvornog koda jednokratno konfigurirati s obzirom na podatke o udruzi i podacima o pošiljatelju:

* u retcima 79-98 treba upisati statične podatke primatelja (udruge), tipično je to:
  * "iban_primatelja": "HR1234567890123456789"
  * "model_primatelja": "HR00"
  * "naziv_primatelja": "Udruga"
  * "ulica_i_broj_primatelja": "Ulica 0"
  * "postanski_i_grad_primatelja": "99999 Grad"
* sender_email (redak 153) sadrži GMail adresu pošiljatelja
* username (redak 158) je Google Account preko kojeg se šalju mailu, tipično je isto kao i GMail adresa pošiljatelja
* password (redak 159) **NIJE password** GMail accounta, nego **Google Application Password** kojeg za aplikaciju treba izgenerirati unutar svog Google Accounta pod opcijom 2FA
* tekst maila s individualiziranim podacima je definiran u redovima 211-231
* kreirati poddirektorij "uplatnice" u koji će se spremati PDF uplatnice, pri čemu će filename bit oblika Uplatnica_ime_prezime_mjesec.pdf

# Korištenje programa

Nakon što se popuni tablica s barem jednim zapisom i barem jednim mjesecom ili razdobljem, tu se tablicu eksportira u CSV formatu u datoteku naziva 'clanarine.csv'.

Nakon toga se program iz komandne linije poziva s npr.

```
./clanarine.py 9-12/2022
```

ili

```
./clanarine.py 6/2023
```

Programu treba nekoliko sekundi za kreiranje i slanje maila po svakom zapisu, pri čemu ispisuje tijek rada:

![image](https://github.com/igustin/ngo_clanarine/assets/1834262/c05f7152-a110-4c9a-8ffb-aa0c5e8a4cb8)

PDF uplatnica imena npr. "Uplatnica_Tomislav_Matić_9-10_2022.pdf" sprema se u poddirektorij "uplatnice" i izgleda ovako:

![image](https://github.com/igustin/ngo_clanarine/assets/1834262/6ede16e3-79fa-4c5c-8e13-b42774e2cea7)

Poslani mail izgleda ovako:

![image](https://github.com/igustin/ngo_clanarine/assets/1834262/a3dd2968-344b-427e-ac7d-e52285eb62b9)

# Credits

Program se bazira na ovim i vezanim rješenjima:
* https://github.com/linuxhr/platne-liste
* https://github.com/linuxhr/hulk-uplatnica
