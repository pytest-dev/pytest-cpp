#include "mocFromCpp.h"

#include <QObject>
#include <stdio.h>

class MyClass1
{
public:
  MyClass1() {};
  void myslot() {};
  void printme()
  {
    printf("It's a Q_OBJECT!");
    printf("Concatenating "
           "a Q_OBJECT"
           " with another "
           "Q_OBJECT"
           "and a "
           "Q_OBJECT, finally");
  };

};

void mocFromCpp()
{
  MyClass1 myclass;
}
