"""
Solution to the one-way tunnel
"""
import time
import random
from multiprocessing import Lock, Condition, Process
from multiprocessing import Value
import colorama

SOUTH = 1
NORTH = 0

NCARS = 100
NPED = 10
TIME_CARS_NORTH = 0.5  # a new car enters each 0.5s
TIME_CARS_SOUTH = 0.5  # a new car enters each 0.5s
TIME_PED = 5 # a new pedestrian enters each 5s
TIME_IN_BRIDGE_CARS = (1, 0.5) # normal 1s, 0.5s
TIME_IN_BRIDGE_PEDESTRIAN = (30, 10) # normal 1s, 0.5s

#Valores para crear un "semáforo" emulando uno real que de paso
E = 1 # Empty
P = 2 # Pedestrians
N = 3 # Car North
S = 4 # Car south

standby_car = 10 # Máximo de coches esperando
standby_ped = 3 # Máximo de peatones esperando

class Monitor():
    def __init__(self):
        self.mutex = Lock()
        self.patata = Value('i', 0)
        
        self.car_north = Value('i', 0) # Número de coches del norte dentro
        self.car_south = Value('i', 0) # Número de coches del sur dentro
        self.car_north_waiting = Value('i', 0) # Número de coches del norte esperando
        self.car_south_waiting = Value('i', 0) # Número de coches del sur esperando
        self.ped = Value('i', 0) # Número de peatones dentro
        self.ped_waiting = Value('i', 0) # Número de peatones esperando
        
        # Condiciones para entrada
        self.cond_car_north = Condition(self.mutex)
        self.cond_car_south = Condition(self.mutex)
        self.cond_ped = Condition(self.mutex)
        # Emulador de semáforo para dar paso
        self.semaphore = Value('i', E) # Estado inicial: Empty

    # Auxiliar, esta instrucción aparece dos veces en las funciones de entrada siguientes
    def not_too_many_ped_waiting(self):
        return self.ped_waiting.value < standby_ped
    

    def car_north_enter(self):
        return (lambda: self.ped.value + self.car_south.value == 0 and \
                       (self.car_south_waiting.value < standby_car and \
                        self.not_too_many_ped_waiting())            or \
                       (self.semaphore.value == N or self.semaphore.value == E))

    def car_south_enter(self):
        return (lambda: self.ped.value + self.car_south.value == 0 and \
                       (self.car_north_waiting.value < standby_car and \
                        self.not_too_many_ped_waiting())            or \
                       (self.semaphore.value == S or self.semaphore.value == E))
    
    def ped_enter(self):
        return (lambda: self.car_north.value + self.car_south.value == 0 and \
                       (self.car_north_waiting.value < standby_car       and \
                        self.car_south_waiting.value < standby_car)       or \
                       (self.semaphore.value == P or self.semaphore.value == E))


    def wants_enter_car(self, direction: int) -> None:
        self.mutex.acquire()
        self.patata.value += 1
        
        if direction == NORTH:
            self.car_north_waiting.value += 1
            print('\033[1;31m' + "South direction, stop")
            self.cond_car_north.wait_for(self.car_north_enter) # Se permite el paso de dirección norte
            print ('\033[1;32m' + "North direction, go ahead" + '\033[39m')
            self.car_north_waiting.value -= 1
        
            if self.semaphore.value == E: # Permitir que pasen unos cuantos del norte seguidamente
                self.semaphore.value = N
                
            self.car_north.value += 1
            
        elif direction == SOUTH:
            self.car_south_waiting.value += 1
            print('\033[1;31m' + "North direction, stop")
            self.cond_car_south.wait_for(self.car_south_enter) # Se permite el paso de dirección sur
            print ('\033[1;32m' + "South direction, go ahead" + '\033[39m')
            self.car_south_waiting.value -= 1
        
            if self.semaphore.value == E: # Permitir que pasen unos cuantos del sur seguidamente
                self.semaphore.value = S
                
            self.car_south.value += 1
        
        self.mutex.release()

    def leaves_car(self, direction: int) -> None:
        self.mutex.acquire() 
        self.patata.value += 1
        
        if direction == NORTH:
            self.car_north.value -= 1
            
            if self.semaphore.value == N:
                
                if self.car_south_waiting.value > 0:
                    self.semaphore.value = S # Momento de paso de unos cuantos coches del sur
                
                elif self.ped_waiting.value > 0:
                    self.semaphore.value = P # Momento de paso de unos cuantos peatones
                
                else:
                    self.semaphore.value = E
                    
            if self.car_north.value == 0: # Se avisa que no hay nadie del norte dentro
                self.cond_car_south.notify_all()
                self.cond_ped.notify_all()
                    
        elif direction == SOUTH:
            self.car_south.value -= 1
            
            if self.semaphore.value == S:
                
                if self.car_north_waiting.value > 0:
                    self.semaphore.value = N # Momento de paso de unos cuantos coches del norte
                    
                elif self.ped_waiting.value > 0:
                    self.semaphore.value = P # Momento de paso de unos cuantos peatones
                    
                else:
                    self.semaphore.value = E
            
            if self.car_south.value == 0: # Se avisa que no hay nadie del sur dentro
                self.cond_car_north.notify_all() 
                self.cond_ped.notify_all()  
        
        self.mutex.release()
        

    def wants_enter_pedestrian(self) -> None:
        self.mutex.acquire()
        self.patata.value += 1
        
        self.ped_waiting.value += 1
        print('\033[1;31m' + "Cars, stop")
        self.cond_ped.wait_for(self.ped_enter)
        print ('\033[1;32m' + "Pedestrians, go ahead" + '\033[39m')
        self.ped_waiting.value -= 1
        
        if self.semaphore.value == E:
            self.semaphore.value = P
            
        self.ped.value += 1
        
        self.mutex.release()

    def leaves_pedestrian(self) -> None:
        self.mutex.acquire()
        self.patata.value += 1
        
        self.ped.value -= 1
        
        if self.semaphore.value == P:
            
            if (lambda: self.car_north_waiting.value > 0 and \
                        self.car_north_waiting.value >= self.car_south_waiting.value):
                self.semaphore.value = N
            
            elif (lambda: self.car_south_waiting.value > 0 and \
                          self.car_south_waiting.value > self.car_north_waiting.value):
                self.semaphore.value = S
            
            else:
                self.semaphore.value = E
        
        if self.ped.value == 0:
            self.cond_car_north.notify_all()
            self.cond_car_south.notify_all() 
            
        self.mutex.release()


    def __repr__(self) -> str:
        return f'Monitor: {self.patata.value}'

def delay_car_north() -> None:
    time.sleep(random.choice(TIME_IN_BRIDGE_CARS))

def delay_car_south() -> None:
    time.sleep(random.choice(TIME_IN_BRIDGE_CARS))

def delay_pedestrian() -> None:
    time.sleep(random.choice(TIME_IN_BRIDGE_PEDESTRIAN))


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

def gen_cars(direction: int, time_cars, monitor: Monitor) -> None:
    cid = 0
    plst = []
    for _ in range(NCARS):
        cid += 1
        p = Process(target=car, args=(cid, direction, monitor))
        p.start()
        plst.append(p)
        time.sleep(random.expovariate(1/time_cars))

    for p in plst:
        p.join()

def main():
    monitor = Monitor()
    gcars_north = Process(target=gen_cars, args=(NORTH, TIME_CARS_NORTH, monitor))
    gcars_south = Process(target=gen_cars, args=(SOUTH, TIME_CARS_SOUTH, monitor))
    gped = Process(target=gen_pedestrian, args=(monitor,))
    gcars_north.start()
    gcars_south.start()
    gped.start()
    gcars_north.join()
    gcars_south.join()
    gped.join()


if __name__ == '__main__':
    main()
