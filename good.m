@interface bad ()
{
}

@property (nonatomic, readonly) NSMutableString *special
@property (atomic, copy) id specialCopy

@end

@implementation bad
@synthesize specialCopy;
@synthesize specialAssign
@synthesize lineNum;
@synthesize temp;
@synthesize foo
@synthesize text;

-(id)init
{
    self = [super init];
    if(self)
    {
        self.foo = [[NSArray alloc] init];
        lineNum = 23;
    }
    return self;
}

-(void) viewDidLoad
{
    special = @"this is text";
    if(self.foo.count == 3)
    {
        NSLog(@"This is a %@", foo);
    }
    else
    {
        self.foo = [NSArray arrayWithObject:@"bar"];
    }
}

-(void)viewDidUnload
{
    self.foo = nil;
    self.text = nil;
    [special release];
    special = nil;
    [super viewDidUnload];
}

+ (BOOL) uninterestingMethod1:(NSString*)str
{
    NSLog("You're not here.");
    assert(YES);
    return NO;
}

- (void) dealloc
{
    [self viewDidUnload];
    self.temp = nil;
    self.specialCopy = nil;
    [foo2 release];
    foo2 = nil;
    [error release];
    error = nil;
    [super dealloc];
}

@end
