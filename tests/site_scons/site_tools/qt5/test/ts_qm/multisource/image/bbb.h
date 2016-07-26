#include <QObject>
#include <QString>

class bbb : public QObject
{
  Q_OBJECT

public:
  bbb();

private:
  QString my_s;
};
