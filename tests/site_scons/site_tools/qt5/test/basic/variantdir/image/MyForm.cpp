#include "MyForm.h"

#include <stdio.h>

MyForm::MyForm(QWidget *parent) : QWidget(parent)
{
  ui.setupUi(this);
}

void MyForm::testSlot()
{
    printf("Hello World\n");
}

