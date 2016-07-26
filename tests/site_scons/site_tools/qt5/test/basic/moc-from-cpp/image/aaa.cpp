#include "aaa.h"

#include <QObject>

class aaa : public QObject
{
  Q_OBJECT

public:
  aaa() {};
};

#include "aaa.moc"

void dummy_a()
{
  aaa a;
}
