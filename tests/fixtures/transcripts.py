"""
Transcriptions de test — exemples réalistes avec bruit conversationnel.
"""

# Cas canonique de la spec projet
SIMPLE_DEGAT_EAUX = (
    "Le 24 février, j'ai eu une fuite d'eau dans ma cuisine "
    "à cause du lave-vaisselle."
)

# Conversation bruitée typique d'un appel téléphonique
NOISY_CONVERSATION = (
    "Bonjour euh oui bonjour madame c'est euh je vous appelle parce que "
    "j'ai eu un problème chez moi euh voilà il y a eu une fuite d'eau "
    "euh le le vingt-quatre février en fait c'est le lave-vaisselle qui a "
    "euh qui a débordé et euh l'eau a coulé partout dans la cuisine et "
    "même un peu dans le salon euh voilà et et mon voisin du dessous "
    "il m'a dit que ça avait coulé chez lui aussi euh je suis propriétaire "
    "je m'appelle Martin Dupont euh voilà"
)

# Incendie — multi-section
INCENDIE_MULTI_SECTION = (
    "Oui bonjour je m'appelle Sophie Bernard je suis propriétaire "
    "d'une maison individuelle de 120 mètres carrés. Le 28 novembre "
    "il y a eu un départ de feu sur la plaque de cuisson dans la cuisine. "
    "L'huile de friture a pris feu euh les pompiers sont intervenus à 22h15. "
    "La cuisine est entièrement détruite et il y a des dégâts de fumée "
    "dans le séjour et le couloir. Le réfrigérateur est fichu aussi, "
    "il était neuf on l'a payé 650 euros."
)

# Vol — avec interruptions
VOL_AVEC_INTERRUPTIONS = (
    "Alors attendez je... oui pardon je reprends. Donc quand on est rentrés "
    "de vacances le 5 janvier la porte d'entrée était fracturée. Ils ont volé "
    "mon ordinateur portable un MacBook Pro et la console PlayStation de mon fils "
    "et aussi des bijoux euh une bague en or un collier et ma montre. "
    "J'ai déposé plainte au commissariat le jour même. Ah oui je suis "
    "locataire dans un T4 au deuxième étage. Jean-Pierre Moreau."
)

# Conversation très courte — peu d'infos
MINIMAL_INFO = "Il y a eu un problème d'eau chez moi la semaine dernière."

# Professionnel — boulangerie
PRO_DEGAT_EAUX = (
    "Bonjour ici c'est la boulangerie Lecomte, SAS Boulangerie Lecomte. "
    "On a eu une rupture de canalisation le 5 février dans le laboratoire "
    "à l'arrière-boutique. C'est la canalisation du mur mitoyen avec "
    "l'appartement du dessus. Le four professionnel Bongard est endommagé "
    "et le pétrin électrique aussi. On a perdu trois jours d'exploitation "
    "et toutes les denrées du matin. Le syndic de copropriété est "
    "responsable puisque c'est une canalisation commune."
)
