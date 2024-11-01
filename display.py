import pygame

class Display:
    def __init__(self, the_world, agent_xA, agent_yA, agent_xB, agent_yB):
        self.cell_size = 20
        self.screen_w = self.cell_size * the_world.get_width()
        self.screen_h = self.cell_size * the_world.get_height()
        self.cells_w = self.screen_w // self.cell_size
        self.cells_h = self.screen_h // self.cell_size
        self.font_size = self.cell_size - 2
        self.agent_size = self.font_size // 2
        self.font_name = "cmuttr.ttf"
        self.agent_color = "#FFFFFF"
        self.agent_facing_color = "#000000"
        self.color_key = {
            'w':'#000000',
            'b':'#0b63d6',
            'o':'#fc9d03',
            'r':'#ab3307',
            'g':'#59eb05',
            'p':'#c708c4',
            'y':'#ffff03',
            '0':'#59eb05',
            '1':'#59eb05',
            '2':'#59eb05',
            '3':'#59eb05',
            '4':'#59eb05',
            '5':'#59eb05',
            '6':'#59eb05',
            '7':'#59eb05',
            '8':'#59eb05',
            '9':'#59eb05',
        }
        self.text = [
            '0', '1', '2', '3', '4',
            '5', '6', '7', '8', '9'
        ]

        pygame.init()
        self.screen = pygame.display.set_mode(
            (self.screen_w, self.screen_h)
        )
        self.run = True
        self.world = the_world
        self.agent_xA = agent_xA
        self.agent_yA = agent_yA
        self.agent_xB = agent_xB
        self.agent_yB = agent_yB
        self.font = pygame.freetype.Font(
            self.font_name, 
            self.font_size
        )

    def update(self, agent_xA, agent_yA, facingA, agent_xB, agent_yB, facingB):
        for event in pygame.event.get():
            pass

        self.agent_xA = agent_xA
        self.agent_yA = agent_yA
        self.agent_xB = agent_xB
        self.agent_yB = agent_yB
        self.screen.fill("black")
        for x in range(0, self.cells_w):
            for y in range(0, self.cells_h):
                if self.world.is_valid_cell(x, y):
                    cell = self.world.get_cell(x, y)
                    pygame.draw.rect(
                        self.screen,
                        self.color_key[cell],
                        pygame.Rect(
                            x*self.cell_size,
                            y*self.cell_size,
                            x*self.cell_size+self.cell_size,
                            y*self.cell_size+self.cell_size
                        )
                    )
                    if cell in self.text:
                        surface, rect = self.font.render(cell)
                        self.screen.blit(
                            surface,
                            (
                                x*self.cell_size + self.cell_size//2 - rect.w//2,
                                y*self.cell_size + self.cell_size//2 - rect.h//2
                            )
                        )

        if self.agent_xA is not None:
            cxA = self.agent_xA*self.cell_size + self.cell_size//2
            cyA = self.agent_yA*self.cell_size + self.cell_size//2

            pygame.draw.circle(
                self.screen,
                self.agent_color,
                (cxA, cyA),
                self.agent_size
            )

            surfaceA, rectA = self.font.render('A')

            self.screen.blit(
                surfaceA,
                (
                    cxA-rectA.w//2,
                    cyA-rectA.h//2
                )
            )
            
        if self.agent_xB is not None:
            cxB = self.agent_xB*self.cell_size + self.cell_size//2
            cyB = self.agent_yB*self.cell_size + self.cell_size//2
        
            pygame.draw.circle(
                self.screen,
                self.agent_color,
                (cxB, cyB),
                self.agent_size
            )
        
            surfaceB, rectB = self.font.render('B')
        
            self.screen.blit(
                surfaceB,
                (
                    cxB-rectB.w//2,
                    cyB-rectB.w//2
                )
            )

        # fx = cxA
        # fy = cyA
        # match facing:
        #     case 'N': fy -= self.agent_size
        #     case 'S': fy += self.agent_size
        #     case 'E': fx += self.agent_size
        #     case 'W': fx -= self.agent_size

        # pygame.draw.line(
        #     self.screen,
        #     self.agent_facing_color,
        #     (cx, cy),
        #     (fx, fy),
        #     2
        # )

        pygame.display.flip()

    def quit(self):
        pygame.quit()
