import json
from flask import Flask, render_template, request, redirect, flash, url_for
from datetime import datetime

def loadClubs():
    with open('clubs.json') as c:
         listOfClubs = json.load(c)['clubs']
         return listOfClubs


def loadCompetitions():
    with open('competitions.json') as comps:
         listOfCompetitions = json.load(comps)['competitions']
         return listOfCompetitions

def is_competition_past(competition_date):
    """Vérifie si une compétition est passée"""
    try:
        competition_datetime = datetime.strptime(competition_date, '%Y-%m-%d %H:%M:%S')
        return competition_datetime < datetime.now()
    except ValueError:
        return True  # Par sécurité si format invalide


app = Flask(__name__)
app.secret_key = 'something_special'

competitions = loadCompetitions()
clubs = loadClubs()

# Cache en mémoire pour accélérer l'affichage du tableau des points
cached_sorted_clubs = []

def refresh_sorted_clubs():
    """Recalcule et met en cache la liste des clubs triée par points (desc)."""
    global cached_sorted_clubs
    try:
        cached_sorted_clubs = sorted(clubs, key=lambda c: int(c.get('points', 0)), reverse=True)
    except Exception:
        cached_sorted_clubs = clubs

# Dictionnaire pour suivre les réservations par club et par compétition
# Structure: {club_name: {competition_name: total_places_booked}}
booking_history = {}

# Préparer le cache au démarrage
refresh_sorted_clubs()

@app.route('/')
def root():
    return render_template('index.html')

@app.route('/index')
def index():
    return render_template('index.html')

# affichage du tableau des points de chaque club sur welcome.html
def get_sorted_clubs():
    """Retourne la liste des clubs triés depuis le cache (refresh ailleurs)."""
    return cached_sorted_clubs, None

@app.route('/showSummary', methods=['POST'])
def showSummary():
    club = [club for club in clubs if club['email'] == request.form['email']][0]
    # affichage du tableau des points de chaque club sur welcome.html
    sorted_clubs, _ = get_sorted_clubs()
    return render_template('welcome.html', club=club, competitions=competitions, clubs=sorted_clubs)


@app.route('/book/<competition>/<club>')
def book(competition, club):
    foundClub = [c for c in clubs if c['name'] == club][0]
    foundCompetition = [c for c in competitions if c['name'] == competition][0]
    
    # Vérification 1: La compétition est-elle passée ?
    if is_competition_past(foundCompetition['date']):
        flash(f'La compétition "{foundCompetition["name"]}" est déjà passée.')
# affichage du tableau des points de chaque club sur welcome.html
        sorted_clubs, _ = get_sorted_clubs()
        return render_template('welcome.html', club=foundClub, competitions=competitions, clubs=sorted_clubs)
    
    if foundClub and foundCompetition:
        # Vérifier si le club a déjà réservé 12 places pour cette compétition
        if foundClub['name'] in booking_history:
            already_booked = booking_history[foundClub['name']].get(foundCompetition['name'], 0)
            if already_booked >= 12:
                flash(f'Vous avez déjà réservé le maximum de 12 places pour la compétition "{foundCompetition["name"]}".')
# affichage du tableau des points de chaque club sur welcome.html
                sorted_clubs, _ = get_sorted_clubs()
                return render_template('welcome.html', club=foundClub, competitions=competitions, clubs=sorted_clubs)
        
        return render_template('booking.html', club=foundClub, competition=foundCompetition)
    else:
        flash("Something went wrong-please try again")
# affichage du tableau des points de chaque club sur welcome.html
        sorted_clubs, _ = get_sorted_clubs()
        return render_template('welcome.html', club=foundClub, competitions=competitions, clubs=sorted_clubs)


@app.route('/purchasePlaces', methods=['POST'])
def purchasePlaces():
    competition = [c for c in competitions if c['name'] == request.form['competition']][0]
    club = [c for c in clubs if c['name'] == request.form['club']][0]
    placesRequired = int(request.form['places'])
    
    # Validation 0: Vérifier si la compétition est passée
    if is_competition_past(competition['date']):
        flash(f'La compétition est déjà passée.')
# affichage du tableau des points de chaque club sur welcome.html
        sorted_clubs, _ = get_sorted_clubs()
        return render_template('welcome.html', club=club, competitions=competitions, clubs=sorted_clubs)
    
    # Validation 1: Vérifier que le nombre de places est positif
    if placesRequired <= 0:
        flash('Le nombre de places doit être supérieur à 0.')
        return render_template('booking.html', club=club, competition=competition)
    
    # Initialiser l'historique pour ce club s'il n'existe pas
    if club['name'] not in booking_history:
        booking_history[club['name']] = {}
    
    # Récupérer le total des places déjà réservées pour cette compétition
    already_booked = booking_history[club['name']].get(competition['name'], 0)
    total_places_after_booking = already_booked + placesRequired
    
    # Validation 2: Vérifier que le total de places (déjà réservées + nouvelles) ne dépasse pas 12
    if total_places_after_booking > 12:
        places_remaining = 12 - already_booked
        if places_remaining > 0:
            flash(f'Vous avez déjà réservé {already_booked} place(s) pour cette compétition. Vous ne pouvez réserver que {places_remaining} place(s) supplémentaire(s) (maximum 12 places par compétition).')
            
        else:
            flash(f'Vous avez déjà réservé 12 places pour cette compétition. Vous ne pouvez plus réserver de places.')
        return render_template('booking.html', club=club, competition=competition)
    
    # Validation 3: Vérifier que le club a suffisamment de points
    club_points = int(club['points'])

    if placesRequired > club_points:
        flash(f'Vous n\'avez pas assez de points. Points disponibles: {club_points}')
        return render_template('booking.html', club=club, competition=competition)
    
    # Validation 4: Vérifier que le nombre de places demandées ne dépasse pas les places disponibles
    available_places = int(competition['numberOfPlaces'])
    if placesRequired > available_places:
        flash(f'Seulement {available_places} place(s) disponible(s) pour cette compétition.')
        return render_template('booking.html', club=club, competition=competition)
    
    # Effectuer la réservation
    competition['numberOfPlaces'] = available_places - placesRequired
    club['points'] = club_points - placesRequired
    
    # Mettre à jour l'historique des réservations
    booking_history[club['name']][competition['name']] = total_places_after_booking

    # Rafraîchir le cache trié suite à la mise à jour des points
    refresh_sorted_clubs()
    
    flash(f'Réservation confirmée! {placesRequired} place(s) réservée(s). Total réservé pour cette compétition: {total_places_after_booking}. Points restants: {club["points"]}')
# affichage du tableau des points de chaque club sur welcome.html
    sorted_clubs, _ = get_sorted_clubs()
    return render_template('welcome.html', club=club, competitions=competitions, clubs=sorted_clubs)


#Tableau des points de chaque club
@app.route('/points')
def points():
    """Page publique affichant le total des points par club (lecture seule)."""
    try:
        sorted_clubs = sorted(clubs, key=lambda c: int(c.get('points', 0)), reverse=True)
    except Exception:
        # En cas de données inattendues, on ne trie pas
        sorted_clubs = clubs
    return render_template('points.html', clubs=sorted_clubs)


@app.route('/welcome/<club_name>')
def welcome(club_name):
    """Accès direct à la page d'accueil d'un club via son nom."""
    foundClub = [c for c in clubs if c['name'] == club_name][0]
    sorted_clubs, _ = get_sorted_clubs()
    return render_template('welcome.html', club=foundClub, competitions=competitions, clubs=sorted_clubs)

def compute_competition_totals(comp_name):
    """Retourne (booked_total, total_places_estime) pour une compétition."""
    booked_total = 0
    for club_name, per_comp in booking_history.items():
        booked_total += int(per_comp.get(comp_name, 0))
    comp = next((c for c in competitions if c['name'] == comp_name), None)
    if not comp:
        return 0, 0
    try:
        available = int(comp.get('numberOfPlaces', 0))
    except Exception:
        available = 0
    total_estimated = available + booked_total
    return booked_total, total_estimated

def compute_competition_status(comp) -> str:
    """Calcule le statut d'inscription en fonction des places et de la date."""
    try:
        available = int(comp.get('numberOfPlaces', 0))
    except Exception:
        available = 0
    past = is_competition_past(comp.get('date', ''))
    if available <= 0:
        return 'complet'
    if past:
        return 'complet'
    if available <= 3:
        return 'presque complet'
    return 'inscriptions ouvertes'

@app.route('/competition/<competition_name>')
def competition_details(competition_name):
    comp = next((c for c in competitions if c['name'] == competition_name), None)
    if not comp:
        flash("Compétition introuvable")
        return redirect(url_for('index'))
    booked_total, total_estimated = compute_competition_totals(competition_name)
    status = compute_competition_status(comp)
    club_name = request.args.get('club')
    foundClub = next((c for c in clubs if c['name'] == club_name), None) if club_name else None
    return render_template('competition_details.html', competition=comp, booked_total=booked_total, total_estimated=total_estimated, status=status, club=foundClub)


@app.route('/logout')
def logout():
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)