#include <bits/stdc++.h>

#define maxn 200005

using namespace std;
typedef long long ll;

int n, m, k;
set<int> g[maxn];
int winLine[maxn];

int main() {
  #define TASK "ABC"
 // freopen(TASK".INP", "r", stdin); //freopen(TASK".OUT", "w", stdout);
  ios_base::sync_with_stdio(0); cin.tie(0); cout.tie(0);

  cin >> n >> m >> k;

    if(n == 1 && m == 1 && k == 0) {
        cout << "Bhinneka";
        return 0;
    }
   if (n == 1 || m == 1) {
      cout << "Chaneka";
      return 0;
  }

  for (int i = 1; i <= k; ++i) {
    int x, y;
    cin >> x >> y;
    g[x].insert(y);
    if (x == 1 || y == 1) {
      cout << "Chaneka";
      return 0;
    }
  }
  int col = m;
  for (int i = n; i > 1; --i) {
    if (col == 0) break;
    if (g[i].empty() || *prev(g[i].end()) < col) {
      g[i].insert(col);
      col--;
    }

    for (auto j : g[i]) {
      winLine[j] = 1;
    }

    while (col > 0 && winLine[col]) col--;
  }

  if (col == 1) cout << "Bhinneka";
  else cout << "Chaneka";

  return 0;
}
