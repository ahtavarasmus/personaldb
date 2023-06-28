#include <stdio.h>
#include <stdlib.h>

struct ship {
    int value;
};
typedef struct ship ship;

ship^ make_ship() {
    ship^ new_ship = (ship^)malloc(sizeof(ship));
    new_ship->value = 10;
    return move new_ship;
}

int main(int argc, char* argv[])
{
    ship^ my_ship = make_ship();
    printf("my_ship->value = %d\n", my_ship->value);
    free(my_ship);

    return 0;
}
