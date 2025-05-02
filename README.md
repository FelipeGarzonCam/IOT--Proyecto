## Segunda Entrega

En la segunda entrega se usó:

- Un sensor ultrasónico que detecta el paso de todas las monedas antes de ser separadas por valor; dicho sensor se refleja en la variable `Pasos Totales`.
- Tres sensores infrarrojos que cuentan la cantidad de monedas de cada denominación: `$1000`, `$200` y `$100`. Ubicados de izquierda a derecha en el montaje.
- Finalmente, tres sensores tipo galga fabricados con velostat y cable UTP, que utilizan los tres pines ADC de la Raspberry Pi Pico. Cada sensor está construido con tres capas de velostat y dos cables entre ellas, y se ubica bajo las cajas que almacenan las monedas ya separadas.
