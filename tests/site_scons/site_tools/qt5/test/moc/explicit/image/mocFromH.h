#include <QObject>

class MyClass2 : public QObject {
  Q_OBJECT;
  public:
  MyClass2();
  public slots:
  void myslot();
};
void mocFromH();

