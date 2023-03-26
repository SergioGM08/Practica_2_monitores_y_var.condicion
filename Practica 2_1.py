"""
Solution to the one-way tunnel
"""
import time
import random
from multiprocessing import Lock, Condition, Process
from multiprocessing import Value

SOUTH = 1
NORTH = 0

NCARS = 100
NPED = 10
TIME_CARS = 0.5  # a new car enters each 0.5s
TIME_PED = 5 # a new pedestrian enters each 5s
TIME_IN_BRIDGE_CARS = (1, 0.5) # normal 1s, 0.5s
TIME_IN_BRIDGE_PEDESTRIAN = (30, 10) # normal 1s, 0.5s

class Monitor():
    def __init__(self):
        self.mutex = Lock()
        self.patata = Value('i', 0)
        
        self.car_north = Value('i', 0) # Número de coches del norte dentro
        self.car_south = Value('i', 0) # Número de coches del sur dentro
        self.ped = Value('i', 0) # Número de peatones dentro

        # Condiciones para entrada
        self.cond_north_car = Condition(self.mutex)
        self.cond_south_car = Condition(self.mutex)
        self.cond_ped = Condition(self.mutex)
         
    def wants_enter_car(self, direction: int) -> None:
        self.mutex.acquire()
        self.patata.value += 1
        
        if direction == NORTH: # Entra si no hay coches ni del sur ni peatones
            self.cond_north_car.wait_for(self.car_south.value + self.ped.value == 0)
            self.car_north.value += 1
            
        elif direction == SOUTH: # Entra si no hay coches del sur ni peatones
            self.cond_south_car.wait_for(self.car_north.value + self.ped.value == 0)
            self.car_south.value += 1
        
        self.mutex.release()

    def leaves_car(self, direction: int) -> None:
        self.mutex.acquire() 
        self.patata.value += 1
        
        if direction == NORTH:
            self.car_north.value -= 1

            if self.car_north.value == 0:
                
                self.cond_south_car.notify_all() # Se avisa que ya no hay coches del norte
                self.cond_ped.notify_all()   
                 
        elif direction == SOUTH:
            self.car_south.value -= 1
            
            if self.car_south.value == 0: # Se avisa que ya no hay coches del sur
                self.cond_north_car.notify_all()
                self.cond_ped.notify_all()  
        
        self.mutex.release()
        
    def wants_enter_pedestrian(self) -> None:
        self.mutex.acquire()
        self.patata.value += 1
        
        # No hay coches dentro, se permite el paso
        self.cond_ped.wait_for(self.car_north.value + self.car_south.value == 0)
        self.ped.value += 1
        
        self.mutex.release()

    def leaves_pedestrian(self) -> None:
        self.mutex.acquire()
        self.patata.value += 1
        
        self.ped.value -= 1
        
        if self.ped.value == 0: # Se avisa que ya no hay peatones
            self.cond_north_car.notify_all()
            self.cond_south_car.notify_all() 
            
        self.mutex.release()

    def __repr__(self) -> str:
        return f'Monitor: {self.patata.value}'

def delay_car_north() -> None:
    time.sleep(random.choice(TIME_IN_BRIDGE_CARS)/10)

def delay_car_south() -> None:
    time.sleep(random.choice(TIME_IN_BRIDGE_CARS)/10)

def delay_pedestrian() -> None:
    time.sleep(random.choice(TIME_IN_BRIDGE_PEDESTRIAN)/10)

def car(cid: int, direction: int, monitor: Monitor)  -> None:
    print(f"Car {cid} heading {direction} wants to enter. {monitor}")
    monitor.wants_enter_car(direction)
    print(f"Car {cid} heading {direction} enters the bridge. {monitor}")
    if direction==NORTH :
        delay_car_north()
    else:
        delay_car_south()
    print(f"Car {cid} heading {direction} leaving the bridge. {monitor}")
    monitor.leaves_car(direction)
    print(f"Car {cid} heading {direction} out of the bridge. {monitor}")

def pedestrian(pid: int, monitor: Monitor) -> None:
    print(f"Pedestrian {pid} wants to enter. {monitor}")
    monitor.wants_enter_pedestrian()
    print(f"Pedestrian {pid} enters the bridge. {monitor}")
    delay_pedestrian()
    print(f"Pedestrian {pid} leaving the bridge. {monitor}")
    monitor.leaves_pedestrian()
    print(f"Pedestrian {pid} out of the bridge. {monitor}")



def gen_pedestrian(monitor: Monitor) -> None:
    pid = 0
    plst = []
    for _ in range(NPED):
        pid += 1
        p = Process(target=pedestrian, args=(pid, monitor))
        p.start()
        plst.append(p)
        time.sleep(random.expovariate(1/TIME_PED))

    for p in plst:
        p.join()

def gen_cars(monitor) -> Monitor:
    cid = 0
    plst = []
    for _ in range(NCARS):
        direction = NORTH if random.randint(0,1)==1  else SOUTH
        cid += 1
        p = Process(target=car, args=(cid, direction, monitor))
        p.start()
        plst.append(p)
        time.sleep(random.expovariate(1/TIME_CARS))

    for p in plst:
        p.join()

def main():
    monitor = Monitor()
    gcars = Process(target=gen_cars, args=(monitor,))
    gped = Process(target=gen_pedestrian, args=(monitor,))
    gcars.start()
    gped.start()
    gcars.join()
    gped.join()


if __name__ == '__main__':
    main()