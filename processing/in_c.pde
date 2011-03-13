import processing.opengl.*;
import traer.physics.*;

final float NODE_SIZE = 50;
final float EDGE_LENGTH = 1; //20;
final float EDGE_STRENGTH = 0.01;
final float SPACER_STRENGTH = 50;
final float SPACER_LENGTH = 1; // 20;
final boolean USE_SPRINGS = true;

final int NUM_PLAYERS = 15;
final int NUM_PIECES = 53;
final int OCTAVE_RANGE = 5;
final int ANCHOR_SPACING = 200;
final int MAX_VELOCITY = 127;
final float VELOCITY_STEP = 0.1;

final color[] COLORS = {
  color(230, 242, 187),
  color(157,181,71),
  color(185,222,52),
  color(198,240,46),
  color(199,255,0)
};

final String[] SAMPLE_NAMES = {"Tom", "Charles", "Julian", "Sommer", "Kriston", "Ficke", "Yglesias", "Kate", "Adam", "Ezra", "Brian", "Jeff", "Erie", "Spencer", "Mandy"};


float aspect_ratio;
float scale = 1;
float centroidX = 0;
float centroidY = 0;

class Player {
  Particle p, parent, name_anchor;
  Spring _spring, _name_spring;
  Attraction _attraction;

  int target_velocity, octave, piece;
  color c;
  float velocity;
  String name;
  float _velocity_pct;

  Player(String p_name, color p_color) {
    octave = 0;
    velocity = 80;
    target_velocity = ceil(velocity);
    piece = 1;
    name = p_name;    
    c = p_color;
    p = physics.makeParticle(1.0, random(0,width), random(0,height), 0);
    name_anchor = physics.makeParticle(1.0, p.position().x(), p.position().y(), 0);
    _name_spring = physics.makeSpring( name_anchor, p, 0.04, EDGE_STRENGTH, 15 );
    parent = null;
    _spring = null;
    _attraction = null;
    _velocity_pct = velocity / float(MAX_VELOCITY);
  }
  
  void set_position(int p_piece, int p_octave) {
    piece = min(NUM_PIECES-1, max(0, p_piece));
    
    int octave_plus_minus = floor(OCTAVE_RANGE/2);
    octave = max(-1*octave_plus_minus, min(octave_plus_minus, p_octave));
    int octave_i = min(OCTAVE_RANGE-1, max(0,(octave + floor(OCTAVE_RANGE/2))));
    Particle new_parent = anchors[piece][octave_i];
    migrate(new_parent);
  }
  
  void migrate(Particle new_parent) {
    parent = new_parent;

    if(USE_SPRINGS) {
      if(_spring!=null) {
        physics.removeSpring(_spring);
      }
      _spring = physics.makeSpring( p, parent, EDGE_STRENGTH, EDGE_STRENGTH, EDGE_LENGTH );
    }
    else {
      if(_attraction!=null) {
        physics.removeAttraction(_attraction);
      }
      
      _attraction = physics.makeAttraction(p, parent, 1000, 10000);
    }
  }
  
  void draw() {
    if(int(velocity)>target_velocity) {
      velocity -= VELOCITY_STEP;
      _velocity_pct = velocity / float(MAX_VELOCITY);
    }
    if(int(velocity)<target_velocity) {
      velocity += VELOCITY_STEP;
      _velocity_pct = velocity / float(MAX_VELOCITY);
    }
    
    
    float ns = _velocity_pct * NODE_SIZE;
    
    noStroke();
    fill(c, 65);
    ellipse( p.position().x(), p.position().y(), ns+4, ns+4);
    fill(c, 210);
    ellipse( p.position().x(), p.position().y(), ns, ns );
    
  }
  
  void draw_name() {
    float radius = ((_velocity_pct * NODE_SIZE) +4) / 2;
 
    pushMatrix();
    translate(p.position().x(), p.position().y());
    float distance = dist(p.position().x(), p.position().y(), name_anchor.position().x(), name_anchor.position().y());
    float ratio = -1.5 * (radius/distance);
    float text_x = (p.position().x() - name_anchor.position().x()) * ratio;
    float text_y = (p.position().y() - name_anchor.position().y()) * ratio;

    // display the name
    fill(255, 255);
    textSize(20 / scale);
    textAlign(CENTER);
    text( name, text_x, text_y);
    textAlign(LEFT);

    // debug particle positions
    //fill(255, 0, 0);
    //ellipse(text_x, text_y, 5, 5);

    popMatrix();

    //fill(0, 255, 0);
    //ellipse(name_anchor.position().x(), name_anchor.position().y(), 5, 5);

    

  }  
}

Particle[][] anchors = new Particle[NUM_PIECES][OCTAVE_RANGE];
Player[] players = new Player[NUM_PLAYERS];

ParticleSystem physics;


void setup()
{
  size( 1024, 768, OPENGL );
  aspect_ratio = float(width) / float(height);
  hint(DISABLE_OPENGL_2X_SMOOTH);
  hint(ENABLE_OPENGL_4X_SMOOTH); //after disabling the 2x this works fine
  smooth(); // this works even better than the 4x! super-smooth! ;)
  strokeWeight( 2 );
  ellipseMode( CENTER );       
  
  physics = new ParticleSystem( 0, 0.1 );
  
  // Runge-Kutta, the default integrator is stable and snappy,
  // but slows down quickly as you add particles.
  // 500 particles = 7 fps on my machine
  physics.setIntegrator( ParticleSystem.MODIFIED_EULER );
    
  // Now try this to see make it more damped, but stable.
  physics.setDrag( 0.6 );
  
  
  setup_players();
    
}

void setup_players() {
  // create anchor nodes  
  int spacer_x = ANCHOR_SPACING;
  int spacer_y = ANCHOR_SPACING;
  for(int i=0;i<NUM_PIECES;i++){
    for(int j=0;j<OCTAVE_RANGE;j++) {
      Particle p = physics.makeParticle(1.0, spacer_x * (i+0.5), spacer_y * (j+0.5), 0);
      p.makeFixed();
      anchors[i][j] = p;      
    }
  }

  

  
  // create players
  for(int i=0;i<NUM_PLAYERS;i++) {
    players[i] = new Player(SAMPLE_NAMES[i % SAMPLE_NAMES.length], COLORS[i % COLORS.length]);    
    players[i].set_position(0, 0);
  }
  
  AddSpacersToAllNodes();
}
  

Particle GetRandomAnchor(){
  return anchors[int(random(0, NUM_PIECES))][int(random(0, OCTAVE_RANGE))];
}

void AddSpacersToAllNodes(){
  for(int i=0;i<players.length;i++) {
    for ( int j=0; j< players.length; j++ ) {
      if ( players[i].p != players[j].p ) {
        // the nodes themselves
        physics.makeAttraction( players[i].p, players[j].p, -SPACER_STRENGTH, SPACER_LENGTH );

        // the name anchors
        physics.makeAttraction( players[i].name_anchor, players[j].name_anchor, -SPACER_STRENGTH, SPACER_LENGTH );        
      }
    }
  }
}

void draw()
{
  physics.tick(); 
  if ( physics.numberOfParticles() > 1 )
    updateCentroid();
  
  background( 0 );
  fill( 128 );
  textSize(12);
  text( "" + physics.numberOfParticles() + " PARTICLES\n" + (int)frameRate + " FPS", 10, 20 );
  translate( width/2 , height/2 );
  scale( scale );
  translate( -centroidX, -centroidY );
 
  drawNetwork();  

  // do something random every second
  if(frameCount%int(frameRate)==0) {
    Player p = players[int(random(0, 256) % players.length)];
    int new_piece = p.piece;
    int new_octave = p.octave;

    // increment or decrement piece randomly
    if (random(1)>0.5) {
      new_piece += 1;
    }
    
    // increment or decrement octave randomly
    if (random(1)>0.5) {      
      if (random(1)>0.5)
        new_octave = new_octave - 1;
      else
        new_octave += 1;
    }
    
    p.set_position(new_piece, new_octave);
    
    // change velocity randomly
    if (random(1)>0.5) {
      p.target_velocity = int(random(0, MAX_VELOCITY));
    }
  }
}

void drawNetwork()
{      
  // draw vertices
  fill( 160 );
  noStroke();
 
 // draw anchors
 /*
 for(int i=0;i<NUM_PIECES;i++) {
   for(int j=0;j<OCTAVE_RANGE;j++) {
     fill(128);
     ellipse(anchors[i][j].position().x(), anchors[i][j].position().y(), 2, 2 );
   }
 }
*/ 
  
  // draw players
  for(int i=0;i<players.length;i++) {
    players[i].draw();
  }

  // draw player names
  for(int i=0;i<players.length;i++) {
    players[i].draw_name();
  }

}

void mousePressed()
{
  // addNode();
}

void mouseDragged()
{
  // addNode();
}

void keyPressed()
{
  if ( key == 'c' )
  {
    initialize();
    return;
  }
  
  if ( key == ' ' )
  {
    players[int(random(0, players.length))].migrate(GetRandomAnchor());

    addNode();
    return;
  }
}

// this assumes a square screen!
void updateCentroid()
{
  float 
    xMax = Float.NEGATIVE_INFINITY, 
    xMin = Float.POSITIVE_INFINITY, 
    yMin = Float.POSITIVE_INFINITY, 
    yMax = Float.NEGATIVE_INFINITY;

  for ( int i = 0; i < players.length; ++i )
  {
    Particle p = players[i].p;
    xMax = max( xMax, p.position().x() );
    xMin = min( xMin, p.position().x() );
    yMin = min( yMin, p.position().y() );
    yMax = max( yMax, p.position().y() );
  }
  float deltaX = xMax-xMin;
  float deltaY = yMax-yMin;
  
  centroidX = xMin + 0.5*deltaX;
  centroidY = yMin +0.5*deltaY;
  
  
  if ( (aspect_ratio*deltaY) > deltaX )
    scale = height/(deltaY+100);
  else
    scale = width/(deltaX+100);

  /*
  // assumes a square window -- we'll just always scale by the smaller dimension
  if ( deltaY > deltaX )
    scale = height/(deltaY+50);
  else
    scale = width/(deltaX+50);
  */
}


void initialize()
{
  physics.clear();
}

void addNode()
{ 
  Particle p = physics.makeParticle();
  Particle q = physics.getParticle( (int)random( 0, physics.numberOfParticles()-1) );
  while ( q == p )
    q = physics.getParticle( (int)random( 0, physics.numberOfParticles()-1) );
  //addSpacersToNode( p, q );
  //makeEdgeBetween( p, q );
  p.position().set( q.position().x() + random( -1, 1 ), q.position().y() + random( -1, 1 ), 0 );
}
