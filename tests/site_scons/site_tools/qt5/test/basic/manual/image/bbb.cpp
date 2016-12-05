#include "bbb.h"

#include <QObject>

class bbb : public QObject
{
  Q_OBJECT

public:
  bbb() {};
};

#include "bbb.moc"

void b_dummy()
{
  bbb b;
}
