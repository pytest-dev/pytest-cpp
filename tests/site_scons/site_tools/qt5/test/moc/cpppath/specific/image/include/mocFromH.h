#include <QObject>

class MyClass2 : public QObject {
  // Here we define a Q_OBJECT
  Q_OBJECT;
  public:
  MyClass2();
  public slots:
  void myslot();
};
void mocFromH();
