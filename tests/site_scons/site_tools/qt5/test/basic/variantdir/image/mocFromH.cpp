#include "mocFromH.h"
    
MyClass2::MyClass2() : QObject() {}
void MyClass2::myslot() {}
void mocFromH() {
  MyClass2 myclass;
}

