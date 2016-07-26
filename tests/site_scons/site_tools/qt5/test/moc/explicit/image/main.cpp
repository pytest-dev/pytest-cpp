#include "mocFromCpp.h"
#include "mocFromH.h"

#include <QtWidgets/QApplication>
#include <stdio.h>
    
int main(int argc, char **argv)
{
  QApplication app(argc, argv);
  mocFromCpp();
  mocFromH();
  printf("Hello World\n");
  return 0;
}
