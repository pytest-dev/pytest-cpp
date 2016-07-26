#include <QObject>

#include "mocFromCpp.h"


/*

class MyClass1 : public QObject {
  Q_OBJECT
  public:
  MyClass1() : QObject() {};
  public slots:
  void myslot() {};
};
void mocFromCpp() {
  MyClass1 myclass;
}
#include "mocFromCpp.moc"

*/

// class MyClass1 : public QObject { Q_OBJECT; };

class MyClass1
{
  // Q_OBJECT

  /* and another Q_OBJECT but in
   * a C comment,
   * ... next Q_OBJECT
   */

public:
  MyClass1() {};
  void myslot() {};
};

void mocFromCpp()
{
  MyClass1 myclass;
}
