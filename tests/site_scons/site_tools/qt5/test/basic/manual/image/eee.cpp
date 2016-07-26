#include <QObject>

class eee : public QObject
{
  Q_OBJECT

public:
  eee() {};
};

#include "moc_eee.cpp"

void e_dummy()
{
  eee e;
}
