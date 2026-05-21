# ⚔️ Heróis do Clique

> *Um clicker épico de fantasia — Clique. Evolua. Vença.*

---

## 📖 Sobre o Jogo

**Heróis do Clique** é um jogo no estilo *clicker RPG* desenvolvido em Python com Pygame. Você é o herói escolhido pela profecia de Clickaria: clique nos monstros, acumule ouro, compre upgrades e derrote o temível Dragão antes que o tempo acabe!

---

## 🎮 Como Jogar

- **Clique no monstro** para causar dano
- Cada monstro morto dropa **Gold** automaticamente
- Use o Gold para comprar **upgrades** no painel esquerdo
- Derrote inimigos suficientes para **avançar de fase**
- **Boss final — Dragão:** derrote-o em **30 segundos** ou volte ao Demon!

---

## 🧟 Inimigos

| Monstro | HP    | Gold Drop | Cenário       |
|---------|-------|-----------|---------------|
| Slime   | 40    | ~2g       | Floresta      |
| Goblin  | 80    | ~5g       | Floresta      |
| Orc     | 160   | ~12g      | Floresta      |
| Demon   | 280   | ~28g      | Campo de Lava |
| Dragon  | 1350  | ~80g      | Covil 🐉      |

---

## ⚡ Upgrades

| Upgrade     | Efeito                                      |
|-------------|---------------------------------------------|
| +Gold/Clique | Ganha gold extra a cada clique              |
| +1 Dano     | Aumenta o dano base do clique               |
| Auto-DPS    | Causa dano automático passivo               |
| Crítico     | +10% de chance de acerto crítico por nível  |

---

## 🛠️ Instalação

### Pré-requisitos

- Python 3.8+
- pip

### Passos

```bash
# Clone o repositório
git clone https://github.com/SEU_USUARIO/herois-do-clique.git
cd herois-do-clique

# Instale as dependências
pip install pygame numpy

# Execute o jogo
python main.py
```

---

## 📁 Estrutura do Projeto

```
herois-do-clique/
├── main.py
├── assets/
│   ├── forest.png
│   ├── lava.png
│   ├── lair.png
│   ├── slime.png
│   ├── goblin.png
│   ├── orc.png
│   ├── demon.png
│   └── dragon.png
└── README.md
```

---

## ✨ Funcionalidades

- 🎵 Música procedural gerada em tempo real por fase
- 🔊 Efeitos sonoros sintetizados (sem arquivos externos)
- ⚙️ Tela de configurações com volume, cores de dano e mute
- 🏆 Galeria de monstros desbloqueáveis para farmar
- 💥 Animações de slash e textos de dano flutuantes
- ⏱️ Timer de 30 segundos no boss final

---

## 🧰 Tecnologias

- [Python](https://python.org)
- [Pygame](https://pygame.org)
- [NumPy](https://numpy.org)

---

## 📜 Lore

*"Há eras, o Reino de Clickaria vivia em paz sob a proteção dos Heróis Antigos. Mas as Sombras acordaram nas profundezas, enviando hordas de monstros. A profecia é clara: um Herói escolhido surgirá, cujo toque carrega o poder de destruir o mal."*

**Esse herói... és tu.**

---

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.
