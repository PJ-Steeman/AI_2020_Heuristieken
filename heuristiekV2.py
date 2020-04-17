# Jelle Caerlen, Kwinten Vanlathem en Pieter-Jan Steeman

import sys
import time
import multiprocessing
import os
import signal
import random
import copy
import math

MAX_ITERATIONS = 750
MAX_T = 750
MIN_T = 20
ALPHA = 0.70

# ---------------------- Klasses ---------------------- #
class Zone:
    def __init__(self):
        self.id = None
        self.adj = None
        self.veh = []
        self.vehNeigh = []

    def setInit(self, id, adjList):
        self.id = id
        self.adj = adjList

    def setVeh(self, list):
        self.veh = list

    def setVehNeigh(self, list):
        self.vehNeigh = list

    def __str__(self):
        return self.id

class Vehicle:
    def __init__(self):
        self.id = None
        self.zone = None

    def setInit(self, line):
        self.id = line[0].rstrip("\n\r")

    def __str__(self):
        return self.id

    def setZone(self, zone):
        self.zone = zone

class Reservation:
    def __init__(self):
        self.id = None
        self.zone = None
        self.day = None
        self.start = None
        self.lenght = None
        self.vehicles = None
        self.p1 = None
        self.p2 = None
        self.assigned_veh = None

    def setInit(self, line):
        self.id = line[0]
        self.zone = line[1]
        self.day = int(line[2])
        self.start = int(line[3])
        self.lenght = int(line[4])
        self.vehicles = line[5].split(",")
        self.p1 = int(line[6])
        self.p2 = int(line[7])
        self.assigned_veh = None

    def __str__(self):
        return self.id

    def setVehicle(self, vehicle):
        self.assigned_veh = vehicle

    def calcCost(self, listVeh):
        if(self.checkSet()):
            if(self.zone == getItem(self.assigned_veh, listVeh).zone):
                return 0
            else:
                return self.p2
        return self.p1

    def checkSet(self):
        return self.assigned_veh is not None

# ---------------------- IO Functies ---------------------- #
def readFile(path):
    # Lege lijsten aanmaken om de objecten in te bewaren
    resList = []
    zoneList = []
    vehList = []

    listIdent = -1
    follower = 0

    file = open(path, "r")

    for line in file:
        # Bij een + karakter naar het volgende soort objecten gaan (Reservaties, Zones en Auto's)
        if(line[0] == "+"):
            listIdent += 1
            follower = 0

            parts = line.split(": ")
            # Het correcte aantal lege objecten van de bijhorende klasse aannmaken
            if(listIdent == 0):
                for i in range(int(parts[1])):
                    resList.append(Reservation())
            if(listIdent == 1):
                for i in range(int(parts[1])):
                    zoneList.append(Zone())
            if(listIdent == 2):
                for i in range(int(parts[1])):
                    vehList.append(Vehicle())

        # Als er geen + staat, de lege objecten vullen met de correcte info
        else:
            # Afhankelijk van de klasse van het object de juiste info verwerken
            if(listIdent == 0):
                resList[follower].setInit(line.split(";"))

            if(listIdent == 1):
                splitLine = line.split(";")
                splitItems = splitLine[1].rstrip("\n\r").split(",")
                zoneList[follower].setInit(splitLine[0], splitItems)

            if(listIdent == 2):
                vehList[follower].setInit(line.split(";"))

            follower += 1

    file.close()
    return vehList, zoneList, resList

def writeFile(path, vehicles, reservations):
    file = open(path, "w")

    # Schrijf de beste cost weg
    file.write(str(calculateCost(reservations, vehicles)) + "\n")

    # Schrijf alle voertuig toewizingen weg
    file.write("+Vehicle assignments\n")
    for veh in vehicles:
        file.write(str(veh).rstrip() + ";" + veh.zone + "\n")

    # Schrijf alle vervulde requests weg
    file.write("+Assigned requests\n")
    for res in reservations:
        if(res.checkSet()):
            file.write(str(res).rstrip() + ";" + res.assigned_veh + "\n")

    # Schrijf alle niet vervulde requests weg
    file.write("+Unassigned requests\n")
    for res in reservations:
        if(not res.checkSet()):
            file.write(str(res) + "\n")
    file.close()

# ---------------------- Hulp Functies ---------------------- #
# Geeft een lijst van de wagens in die zone terug
def getVehicleInZone(zone, listVeh, listZone):
    listVehInZone = []
    for veh in listVeh:
        if(veh.zone == str(zone)):
            listVehInZone.append(str(veh))
    return listVehInZone

# Geeft een lijst van de wagens in de buurzone's terug
def getVehicleInNeighbour(zone, listZone):
    listVehInNeigh = []
    for zo in zone.adj:
        listVehInNeigh.append(getItem(zo, listZone).veh)
    return listVehInNeigh

# Berekent de totale kost van een oplossing
def calculateCost(resList, listVeh):
    cost = 0
    for res in resList:
        cost += res.calcCost(listVeh)
    return cost

# Controleert of een wagen op dat een bepaald tijdstip en in die zone vrij is
def checkCarAvailable(veh, listRes, req):

    if (str(veh) not in req.vehicles):
        return False
    vehRange = range(req.start, req.start + req.lenght)
    for fixed in listRes:
        if (str(veh) == fixed.assigned_veh):
            if (req.day != fixed.day):
                continue
            fixedRange = range(fixed.start, fixed.start + fixed.lenght)
            if (len(list(set(vehRange) & set(fixedRange))) > 1):
                return False
    return True

# Zet string id's om naar hun corresponderende objecten
def getItem(id, list):
    for item in list:
        if(item.id == id):
            return item
    return None
# ---------------------- Toewijzings Functies ---------------------- #
# Geeft aan alle auto's in de randomAssigList een random zone en past de auto lijsten in de zone en zijn buren aan
def randomAssignment(listZone, listRes, listVeh, randomAssigList = None):
    if(randomAssigList == None):
        randomAssigList = listVeh

    for veh in randomAssigList:
        vehFromList = getItem(str(veh), listVeh)
        vehFromList.setZone(str(listZone[random.randrange(0, len(listZone))]))
        # print(str(veh) + " staat in zone " + str(veh.zone))

    for zone in listZone:
        zone.setVeh(getVehicleInZone(zone, listVeh, listRes))
        # print(getVehicleInZone(zone, listVeh, listRes))

    for zone in listZone:
        zone.setVehNeigh(getVehicleInNeighbour(zone, listZone))

    # print(listZone[0].veh + listZone[1].veh + listZone[2].veh)

    return listZone, listRes, listVeh

# Vervult zo veel mogelijk request
def requestFiller(listZone, listRes, listVeh):
    # Bepaal een random volgorde om de requests te vervullen
    shuffeledList = list(range(len(listRes)))
    random.shuffle(shuffeledList)

    for r_id in shuffeledList:
        found = False
        # Vervul enkel nog niet geassignde requets
        if listRes[r_id].assigned_veh == None:

            # Kijk eerst of er nog een auto binnen de zone vrij is
            # print(getItem(listRes[r_id].zone, listZone).veh)
            if(len(getItem(listRes[r_id].zone, listZone).veh) != 0):
                random.shuffle(getItem(listRes[r_id].zone, listZone).veh)
                for veh in getItem(listRes[r_id].zone, listZone).veh:
                    if(checkCarAvailable(veh, listRes, listRes[r_id])):
                        listRes[r_id].setVehicle(str(veh))
                        # print("assigned - 1")
                        found = True
                        break

            # Kijk of er een auto bij een van de buren vrij is
            if(len(getItem(listRes[r_id].zone, listZone).vehNeigh) != 0):
                if not found:
                    random.shuffle(getItem(listRes[r_id].zone, listZone).vehNeigh)
                    for veh in getItem(listRes[r_id].zone, listZone).vehNeigh:
                        if(checkCarAvailable(veh, listRes, listRes[r_id])):
                            listRes[r_id].setVehicle(str(veh))
                            # print("assigned - 2")
                            break

    return listZone, listRes

# ---------------------- Random Functies ---------------------- #
def randomChange(listRes, listZone, listVeh):
    i = random.randrange(4)
    if (i < 2):
        # Unassign een request
        listZone, listRes = requestUnassignment(listZone, listRes)
        listZone, listRes = requestFiller(listZone, listRes, listVeh)
    if (i >= 2):
        # Assign wagen aan andere zone
        listZone, listRes, listVeh = zoneReassignment(listZone, listRes, listVeh)
        listZone, listRes = requestFiller(listZone, listRes, listVeh)
    return True, listRes, listZone, listVeh

def zoneReassignment(listZone, listRes, listVeh):
    veh = listVeh[random.randrange(0, len(listVeh))]

    for res in listRes:
        if str(res.assigned_veh) == str(veh):
            res.setVehicle(None)

    listZone, listRes, listVeh = randomAssignment(listZone, listRes, listVeh, [veh])

    return listZone, listRes, listVeh

def requestUnassignment(listZone, listRes):
    request = listRes[random.randrange(0, len(listRes))]
    request.setVehicle(None)
    return listZone, listRes

# ---------------------- SOLVER ---------------------- #
def solver(queue: multiprocessing.Queue, listZone, listRes, listVeh, seed, pathOut):

    total_best_cost = None
    total_best_zone = None
    total_best_res = None
    total_best_veh = None

    if(int(sys.argv[4]) != 0):
        random.seed(seed)
    else:
        random.seed(None)

    stop = False

    try:
        while not stop:

            # Backups maken waar uiteindelijk de best oplossing in zal komen
            zoneBackup = copy.deepcopy(listZone)
            resBackup = copy.deepcopy(listRes)
            vehBackup = copy.deepcopy(listVeh)

            # Maak een initiële oplossing (volledig random)
            listZone, listRes, listVeh = randomAssignment(listZone, listRes, listVeh)

            # initiële random toewijzing van requests
            listZone, listRes = requestFiller(listZone, listRes, listVeh)

            best_cost = calculateCost(listRes, listVeh)

            T = MAX_T

            # Simulated annealing
            while T >= MIN_T:
                for it in range(MAX_ITERATIONS):
                    # Voer een verandering uit
                    changeWorked, listRes, listZone, listVeh = randomChange(listRes, listZone, listVeh)
                    if(changeWorked):
                        current_cost = calculateCost(listRes, listVeh)
                        dE = current_cost - best_cost

                        # Als de nieuwe oplossing beter is of gelukt heeft werken we er op verder
                        if (dE <= 0) or (math.exp((-dE)/T) > random.random()):
                            best_cost = current_cost
                            zoneBackup = copy.deepcopy(listZone)
                            resBackup = copy.deepcopy(listRes)
                            vehBackup = copy.deepcopy(listVeh)

                        # Als er geen verbetering is en de oplossing heeft geen geluk, zullen we verdergaan van onze laatster beste oplossing
                        else:
                            listZone = copy.deepcopy(zoneBackup)
                            listRes = copy.deepcopy(resBackup)
                            listVeh = copy.deepcopy(vehBackup)

                T = ALPHA * T
                print(T)

            if (total_best_cost is None or best_cost < total_best_cost):
                print("verbetering van " + str(total_best_cost) + " naar " + str(best_cost))
                total_best_cost = best_cost
                total_best_res = copy.deepcopy(listRes)
                total_best_zone = copy.deepcopy(listZone)
                total_best_veh = copy.deepcopy(listVeh)

                writeFile(pathOut, total_best_veh, total_best_res)

    except (KeyboardInterrupt):
        pass

# ---------------------- MAIN ---------------------- #
def main():
    # Start de timer
    start_time = time.time()

    # Verwerking van de argumenten
    pathIn = sys.argv[1]
    pathOut = sys.argv[2]
    max_time = int(sys.argv[3])

    if(len(sys.argv) == 6):
        max_thread = int(sys.argv[5])
    else:
        max_thread = 1

    print("Input file: " + pathIn + "   -----   Output file: " + pathOut + "   -----   Maximum runtime: " + str(max_time) + "   -----   Aantal threads: " + str(max_thread))

    # Het inlezen van de inpufile en in een lijst van objecten zetten
    listVeh, listZone, listRes = readFile(pathIn)

    read_time = time.time() - start_time
    print("Tijd gebruikt om file in te lezen: " + str(read_time) + " sec.")

    # Maak een queue voode communicatie met de main en maak de verschillende threads
    queue = multiprocessing.Queue()
    threads = [multiprocessing.Process(target = solver, args=(queue, listZone, listRes, listVeh, int(sys.argv[4]) * (i+1), pathOut+str(i))) for i in range (max_thread)]

    for t in threads:
        t.start()

    # Kill de threads iets voor de tijd verlopen is
    sleep_time = max_time - 4 * read_time - .5

    if(sleep_time < 0):
        sleep_time = 60*60

    try:
        time.sleep(sleep_time)
    except (KeyboardInterrupt):
        pass

    for t in threads:
        os.kill(t.pid, signal.SIGINT)

    # Haal alle oplossingen op

    fileList = [pathOut+str(i) for i in range(max_thread)]
    scoreList = []

    for f in fileList:
        file = open(f)
        scoreList.append(int(file.readline().rstrip("\n\r")))
        file.close()

    print("rename: " + fileList[scoreList.index(min(scoreList))])
    try:
        os.remove(pathOut)
    except:
        pass
    os.rename(fileList[scoreList.index(min(scoreList))], pathOut)

    for file in fileList:
        print("remove: " + file)
        try:
            os.remove(file)
        except:
            pass

    print(" --------------------- BESTE OPLOSING: " + str(min(scoreList)) + " --------------------- ")
    print(" --------------------- TOTALE DUUR: " + str(time.time() - start_time) + " --------------------- ")

if __name__ == '__main__':
    main()