#include "mocFromCpp.h"
#include "mocFromH.h"
#include "MyForm.h"

#include <QtWidgets/QApplication>
#include <stdio.h>
    
int main(int argc, char **argv) {
  QApplication app(argc, argv);
  mocFromCpp();
  mocFromH();
  MyForm mywidget;
  mywidget.testSlot();
  printf("Hello World\n");
  return 0;
}

