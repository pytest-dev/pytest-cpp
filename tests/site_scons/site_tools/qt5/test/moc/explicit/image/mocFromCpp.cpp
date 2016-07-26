#include <QObject>

#include "mocFromCpp.h"

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
#include "explicitly_moced_FromCpp.strange_cpp_moc_prefix"

