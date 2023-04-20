# Practica_2_monitores_y_var.condicion
Dos versiones: la primera con inanición, la segunda sin ella.

Primera versión:
Se suma y resta una unidad si un elemento ha entrado en el puente, sólo accediendo a él si no hay otros elementos que no lo permitan, como elementos en sentido contrario o peatones, que pueden ir en ambos sentidos a la vez.
Se hace uso de locks para que la entrada sea de a uno y las variables condición, y al salir se notifica para que las variables condición permitan de nuevo la entrada del elemento correspondiente siguiendo las indicaciones del enunciado.

Segunda versión:
La base es la misma solo que se añade a las variables condición un "semáforo" que de paso por turnos. Entrarán también bajo la condición de que no haya demasiados elementos en una de las entradas esperando

Invariante:
Se especifica el invariante y dónde se cumple tras los incrementos y decrementos de los Value, asegurando la oportunidad de entrada de cada tipo de elemento y la seguridad de paso.



