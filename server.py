import json
from flask import Flask,render_template,request,redirect,flash,url_for


def loadClubs():
    with open('clubs.json') as c:
         listOfClubs = json.load(c)['clubs']
         return listOfClubs


def loadCompetitions():
    with open('competitions.json') as comps:
         listOfCompetitions = json.load(comps)['competitions']
         return listOfCompetitions


app = Flask(__name__)
app.secret_key = 'something_special'

competitions = loadCompetitions()
clubs = loadClubs()

# Dictionnaire pour tracker les réservations par club et compétition
# Structure: {club_name: {competition_name: total_places_reserved}}
club_reservations = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/showSummary',methods=['POST'])
def showSummary():
    club = [club for club in clubs if club['email'] == request.form['email']][0]
    return render_template('welcome.html',club=club,competitions=competitions)


@app.route('/book/<competition>/<club>')
def book(competition,club):
    foundClub = [c for c in clubs if c['name'] == club][0]
    foundCompetition = [c for c in competitions if c['name'] == competition][0]
    if foundClub and foundCompetition:
        return render_template('booking.html',club=foundClub,competition=foundCompetition)
    else:
        flash("Something went wrong-please try again")
        return render_template('welcome.html', club=club, competitions=competitions)


@app.route('/purchasePlaces',methods=['POST'])
def purchasePlaces():
    competition = [c for c in competitions if c['name'] == request.form['competition']][0]
    club = [c for c in clubs if c['name'] == request.form['club']][0]
    placesRequired = int(request.form['places'])
    
    club_name = club['name']
    competition_name = competition['name']
    
    # Initialiser le tracking des réservations si nécessaire
    if club_name not in club_reservations:
        club_reservations[club_name] = {}
    if competition_name not in club_reservations[club_name]:
        club_reservations[club_name][competition_name] = 0
    
    # Calculer le total de places déjà réservées pour cette compétition
    places_already_reserved = club_reservations[club_name][competition_name]
    total_places_after_reservation = places_already_reserved + placesRequired
    
# Validation 1: Vérifier que le club a suffisamment de points
    club_points = int(club['points'])
    if placesRequired > club_points:
        flash(f'Vous n\'avez pas assez de points. Points disponibles: {club_points}')
        return render_template('booking.html', club=club, competition=competition)
    
# Validation 2: Vérifier que le total des places (actuelles + précédentes) ne dépasse pas 12
    if total_places_after_reservation > 12:
        places_remaining = 12 - places_already_reserved
        if places_remaining <= 0:
            flash(f'Vous avez déjà réservé le maximum de 12 places pour cette compétition.')
        else:
            flash(f'Vous ne pouvez réserver que {places_remaining} place(s) supplémentaire(s) pour cette compétition (déjà réservé: {places_already_reserved}).')
        return render_template('booking.html', club=club, competition=competition)
    
# Validation 3: Vérifier que le nombre de places demandées ne dépasse pas les places disponibles
    available_places = int(competition['numberOfPlaces'])
    if placesRequired > available_places:
        flash(f'Seulement {available_places} places disponibles pour cette compétition.')
        return render_template('booking.html', club=club, competition=competition)
    
# Validation 4: Vérifier que le nombre de places est positif
    if placesRequired <= 0:
        flash('Le nombre de places doit être supérieur à 0.')
        return render_template('booking.html', club=club, competition=competition)
    
    # Effectuer la réservation
    competition['numberOfPlaces'] = int(competition['numberOfPlaces']) - placesRequired
    club['points'] = club_points - placesRequired
    
    # Mettre à jour le tracking des réservations
    club_reservations[club_name][competition_name] += placesRequired

    flash(f'Réservation confirmée! {placesRequired} place(s) réservée(s). Total réservé pour cette compétition: {club_reservations[club_name][competition_name]}. Points restants: {club["points"]}')
    return render_template('welcome.html', club=club, competitions=competitions)


# TODO: Add route for points display


@app.route('/logout')
def logout():
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)