#include <QObject>
#include <stdio.h>

class MyClass2
{
public:
  MyClass2();
  void myslot();
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

void mocFromH();
