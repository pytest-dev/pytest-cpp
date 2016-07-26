#include <QObject>
#include <QString>

class aaa : public QObject
{
  Q_OBJECT

public:
  aaa();

private:
  QString my_s;
};
