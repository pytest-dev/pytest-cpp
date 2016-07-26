#include <QObject>

/*
class MyClass2 : public QObject {
  // Here we define a Q_OBJECT
  Q_OBJECT;
  public:
  MyClass2();
  public slots:
  void myslot();
};
void mocFromH();

*/

// class MyClass2 : public QObject { Q_OBJECT; };

class MyClass2
{
  // Q_OBJECT

  /* and another Q_OBJECT but in
   * a C comment,
   * ... next Q_OBJECT
   */

public:
  MyClass2();
  void myslot();
};

void mocFromH();
